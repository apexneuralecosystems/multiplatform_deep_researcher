import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Literal, Optional

from crewai import Agent, Crew, LLM, Task
from crewai.flow.flow import Flow, listen, start
from crewai_tools import MCPServerAdapter
from dotenv import load_dotenv
from mcp import StdioServerParameters
from pydantic import BaseModel, Field, HttpUrl

load_dotenv()

print("DEBUG: flow.py module loaded", flush=True)

# ---------- Pydantic Schemas ----------
Platform = Literal["instagram", "linkedin", "youtube", "x", "web"]


class URLBuckets(BaseModel):
    instagram: List[str] = Field(default_factory=list)
    linkedin: List[str] = Field(default_factory=list)
    youtube: List[str] = Field(default_factory=list)
    x: List[str] = Field(default_factory=list)
    web: List[str] = Field(default_factory=list)


class SpecialistOutput(BaseModel):
    platform: Platform
    url: str
    summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------- Flow State ----------
class DeepResearchFlowState(BaseModel):
    query: str = ""
    final_response: Optional[str] = None


# ---------- MCP Server Configurations ----------
def server_params() -> StdioServerParameters:
    token = os.getenv("BRIGHT_DATA_API_TOKEN")
    if not token:
        raise RuntimeError("BRIGHT_DATA_API_TOKEN is not set")
    
    # Check for local node_modules installation
    local_script = os.path.join(os.getcwd(), "node_modules", "@brightdata", "mcp", "server.js")
    
    if os.path.exists(local_script):
        logging.info(f"Found local MCP server script: {local_script}")
        return StdioServerParameters(
            command="node",
            args=[local_script],
            env={"API_TOKEN": token, "PRO_MODE": "true"},
        )
    else:
        logging.warning("Local MCP server script not found, falling back to npx")
        return StdioServerParameters(
            command="npx",
            args=["-y", "@brightdata/mcp"],
            env={"API_TOKEN": token, "PRO_MODE": "true"},
        )


# ---------- Flow Definition ----------
class DeepResearchFlow(Flow[DeepResearchFlowState]):
    search_llm: Any = LLM(
        model="openrouter/openai/gpt-4o",
        temperature=0.0,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )
    specialist_llm: Any = LLM(
        model="openrouter/openai/o3-mini",
        temperature=0.1,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )
    response_llm: Any = LLM(
        model="openrouter/google/gemini-2.0-flash-001",
        temperature=0.3,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )

    @start()
    def start_flow(self) -> Dict[str, Any]:
        """Start the flow by setting the query in the state."""
        # Entry: state.query already populated by caller
        return {"query": self.state.query}
    @listen(start_flow)
    def collect_urls(self) -> Dict[str, Any]:
        """Search web for user query and return URLBuckets object."""
        with open("debug.log", "a", encoding="utf-8") as f: f.write("DEBUG: Starting collect_urls step\n")
        try:
            with MCPServerAdapter(server_params()) as mcp_tools:
                with open("debug.log", "a", encoding="utf-8") as f: f.write("DEBUG: MCPServerAdapter initialized for collect_urls\n")
                search_agent = Agent(
                    role="Multiplatform Web Discovery Specialist",
                    goal=(
                        "Your objective is to identify and return a well-organized JSON object containing only public, directly relevant links for a given user query. "
                        "The links should be grouped by platform: Instagram, LinkedIn, YouTube, X (formerly Twitter), and the open web."
                    ),
                    backstory=(
                        "You are an expert web researcher skilled in using advanced search operators and platform-specific techniques. "
                        "You rigorously verify that every link is public, accessible, and highly relevant to the query. "
                        "You never include duplicates or irrelevant results, and you never fabricate information. "
                        "If no suitable links are found for a platform, you return an empty list for that platform. "
                        "Your output is always precise, clean, and strictly follows the required schema."
                    ),
                    tools=[mcp_tools["search_engine"]],
                    llm=self.search_llm,
                )

                search_task = Task(
                    description=f"""
You are collecting public URLs for this query: "{self.state.query}".

Return ONLY a JSON object matching the URLBuckets schema with EXACT keys:
["instagram","linkedin","youtube","x","web"], each a list of HTTPS URLs.

Classification rules (strict):
- instagram:       instagram.com/*
- linkedin:        linkedin.com/*
- youtube:         youtube.com/*
- x:               x.com/* or twitter.com/*
- web:             only web pages that opens to an article or blog post (exclude the above domains and landing pages)

Quality + validity:
- No duplicates within or across lists.
- Cap each list at 3 URLs, ordered by likely usefulness.

If a platform yields nothing, return an empty list [] for that key.
Output must be pure JSON, no code fences, no commentary.

Example shape (not a template):
{{"instagram":[], "linkedin":[], "youtube":[], "x":[], "web":[]}}
""",
                    agent=search_agent,
                    output_pydantic=URLBuckets,  # Enforces the schema
                    expected_output="Strict JSON for URLBuckets. No extra text or formatting.",
                )

                crew = Crew(agents=[search_agent], tasks=[search_task], verbose=True)
                with open("debug.log", "a", encoding="utf-8") as f: f.write("DEBUG: Kickoff search crew\n")
                out: URLBuckets = crew.kickoff()
                with open("debug.log", "a", encoding="utf-8") as f: f.write(f"DEBUG: Search crew finished. URLs found: {out}\n")
                return {"urls_buckets": out.model_dump(mode="raw")}

        except Exception as e:
            with open("debug.log", "a", encoding="utf-8") as f: f.write(f"DEBUG: collect_urls failed: {e}\n")
            empty = URLBuckets().model_dump(mode="raw")
            return {"urls_buckets": empty, "error": f"{e}"}

    @listen(collect_urls)
    async def dispatch_to_specialists(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Fan-out to platform specialists. Each platform is processed independently and in parallel."""
        with open("debug.log", "a", encoding="utf-8") as f: f.write("DEBUG: Starting dispatch_to_specialists step\n")
        
        # Helper to process a single platform bucket
        async def _process_platform(
            platform: Platform, urls: List[HttpUrl]
        ) -> List[SpecialistOutput]:
            with open("debug.log", "a", encoding="utf-8") as f: f.write(f"DEBUG: Processing platform: {platform} with {len(urls)} URLs\n")
            # Check if no URLs are provided
            if not urls:
                # Skip the function if no URLs are provided
                with open("debug.log", "a", encoding="utf-8") as f: f.write(f"DEBUG: Skipping {platform} due to empty URLs\n")
                return []

            # Note: MCPServerAdapter usage might need to be careful in async if it's not async-aware
            # But since we are creating a new instance per task, it should be fine as long as it doesn't rely on global state that conflicts.
            # We use asyncio.to_thread for the synchronous parts if needed, but CrewAI's kickoff_async should handle the heavy lifting.
            # However, MCPServerAdapter context manager is synchronous. 
            # We will wrap the setup in the async function.
            
            try:
                with MCPServerAdapter(server_params()) as mcp_tools:
                    with open("debug.log", "a", encoding="utf-8") as f: f.write(f"DEBUG: MCPServerAdapter initialized for {platform}\n")
                    tools_map: Dict[str, List[Any]] = {
                        "instagram": [mcp_tools["web_data_instagram_posts"]],
                        "linkedin": [mcp_tools["web_data_linkedin_posts"]],
                        "youtube": [mcp_tools["web_data_youtube_videos"]],
                        "x": [mcp_tools["web_data_x_posts"]],
                        "web": [mcp_tools["scrape_as_markdown"]],
                    }

                    specialist_research_agent = Agent(
                        role=f"{platform.capitalize()} Specialist Research Agent",
                        goal=(
                            f"You are a {platform.capitalize()} deep content analysis/research specialist. "
                            f"Given one or more public {platform} URLs, your task is to extract high-signal facts, "
                            "insights, and key information from the content. "
                            "For each URL, return a strictly valid object (no extra attributes, no commentary) matching the output schema."
                        ),
                        backstory=(
                            "You operate with deep-research rigor and platform expertise. "
                            "Never speculate or infer beyond what is directly available. "
                            "Prioritize accuracy, clarity, and completeness in your extraction, and always adhere to the output schema."
                        ),
                        tools=tools_map[platform],
                        llm=self.specialist_llm,
                    )

                    # One task per URL to keep outputs atomic and typed
                    specialist_research_task = Task(
                        description=f"""
Process this {platform} URL: {urls}

Requirements:
- Use the provided tools to fetch content only.
- Summarize in bullet points ~500-750 words total (avoid fluff).
- Do not fabricate fields; leave unknowns out.

Output:
- Return ONLY valid JSON matching SpecialistOutput schema:
  {{ "platform": "{platform}", "url": "<canonical_url>", "summary": "<summary>", "metadata": {{...}} }}
""",
                        agent=specialist_research_agent,
                        output_pydantic=SpecialistOutput,
                        expected_output="Strict JSON for SpecialistOutput; no prose, no code fences.",
                    )

                    crew = Crew(
                        agents=[specialist_research_agent],
                        tasks=[specialist_research_task],
                        verbose=True,
                    )
                    # Use kickoff_async for parallel execution
                    with open("debug.log", "a", encoding="utf-8") as f: f.write(f"DEBUG: Kickoff specialist crew for {platform}\n")
                    platform_output: SpecialistOutput = await crew.kickoff_async()
                    with open("debug.log", "a", encoding="utf-8") as f: f.write(f"DEBUG: Specialist crew for {platform} finished\n")
                    return [platform_output]
            except Exception as e:
                with open("debug.log", "a", encoding="utf-8") as f: f.write(f"DEBUG: Error in _process_platform for {platform}: {e}\n")
                raise e

        # Process each platform bucket with clear failure isolation
        url_buckets_dict = (
            json.loads(inputs["urls_buckets"]["raw"])
            if isinstance(inputs["urls_buckets"]["raw"], str)
            else inputs["urls_buckets"]["raw"]
        )

        tasks = []
        platforms = []

        for platform, bucket in url_buckets_dict.items():
            tasks.append(_process_platform(platform, bucket))
            platforms.append(platform)

        # Run all tasks in parallel
        with open("debug.log", "a", encoding="utf-8") as f: f.write(f"DEBUG: Dispatching {len(tasks)} platform tasks\n")
        results_raw = await asyncio.gather(*tasks, return_exceptions=True)
        with open("debug.log", "a", encoding="utf-8") as f: f.write("DEBUG: All platform tasks completed\n")
        
        results: List[SpecialistOutput] = []
        
        for i, result in enumerate(results_raw):
            platform = platforms[i]
            if isinstance(result, Exception):
                with open("debug.log", "a", encoding="utf-8") as f: f.write(f"DEBUG: {platform} specialist failed: {result}\n")
                results.append(
                    SpecialistOutput(
                        platform=platform,
                        url="https://invalid.local",
                        summary=f"Error: {type(result).__name__}",
                        metadata={"detail": str(result)},
                    )
                )
            else:
                # result is List[SpecialistOutput]
                results.extend(result)

        return {"specialist_results": results}
        try:
            with MCPServerAdapter(server_params()) as mcp_tools:
                print("DEBUG: MCPServerAdapter initialized for collect_urls", flush=True)
                search_agent = Agent(
                    role="Multiplatform Web Discovery Specialist",
                    goal=(
                        "Your objective is to identify and return a well-organized JSON object containing only public, directly relevant links for a given user query. "
                        "The links should be grouped by platform: Instagram, LinkedIn, YouTube, X (formerly Twitter), and the open web."
                    ),
                    backstory=(
                        "You are an expert web researcher skilled in using advanced search operators and platform-specific techniques. "
                        "You rigorously verify that every link is public, accessible, and highly relevant to the query. "
                        "You never include duplicates or irrelevant results, and you never fabricate information. "
                        "If no suitable links are found for a platform, you return an empty list for that platform. "
                        "Your output is always precise, clean, and strictly follows the required schema."
                    ),
                    tools=[mcp_tools["search_engine"]],
                    llm=self.search_llm,
                )

                search_task = Task(
                    description=f"""
You are collecting public URLs for this query: "{self.state.query}".

Return ONLY a JSON object matching the URLBuckets schema with EXACT keys:
["instagram","linkedin","youtube","x","web"], each a list of HTTPS URLs.

Classification rules (strict):
- instagram:       instagram.com/*
- linkedin:        linkedin.com/*
- youtube:         youtube.com/*
- x:               x.com/* or twitter.com/*
- web:             only web pages that opens to an article or blog post (exclude the above domains and landing pages)

Quality + validity:
- No duplicates within or across lists.
- Cap each list at 3 URLs, ordered by likely usefulness.

If a platform yields nothing, return an empty list [] for that key.
Output must be pure JSON, no code fences, no commentary.

Example shape (not a template):
{{"instagram":[], "linkedin":[], "youtube":[], "x":[], "web":[]}}
""",
                    agent=search_agent,
                    output_pydantic=URLBuckets,  # Enforces the schema
                    expected_output="Strict JSON for URLBuckets. No extra text or formatting.",
                )

                crew = Crew(agents=[search_agent], tasks=[search_task], verbose=True)
                print("DEBUG: Kickoff search crew", flush=True)
                out: URLBuckets = crew.kickoff()
                print(f"DEBUG: Search crew finished. URLs found: {out}", flush=True)
                return {"urls_buckets": out.model_dump(mode="raw")}

        except Exception as e:
            print(f"DEBUG: collect_urls failed: {e}", flush=True)
            empty = URLBuckets().model_dump(mode="raw")
            return {"urls_buckets": empty, "error": f"{e}"}

    @listen(collect_urls)
    async def dispatch_to_specialists(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Fan-out to platform specialists. Each platform is processed independently and in parallel."""
        print("DEBUG: Starting dispatch_to_specialists step", flush=True)
        
        # Helper to process a single platform bucket
        async def _process_platform(
            platform: Platform, urls: List[HttpUrl]
        ) -> List[SpecialistOutput]:
            print(f"DEBUG: Processing platform: {platform} with {len(urls)} URLs", flush=True)
            # Check if no URLs are provided
            if not urls:
                # Skip the function if no URLs are provided
                print(f"DEBUG: Skipping {platform} due to empty URLs", flush=True)
                return []

            # Note: MCPServerAdapter usage might need to be careful in async if it's not async-aware
            # But since we are creating a new instance per task, it should be fine as long as it doesn't rely on global state that conflicts.
            # We use asyncio.to_thread for the synchronous parts if needed, but CrewAI's kickoff_async should handle the heavy lifting.
            # However, MCPServerAdapter context manager is synchronous. 
            # We will wrap the setup in the async function.
            
            try:
                with MCPServerAdapter(server_params()) as mcp_tools:
                    print(f"DEBUG: MCPServerAdapter initialized for {platform}", flush=True)
                    tools_map: Dict[str, List[Any]] = {
                        "instagram": [mcp_tools["web_data_instagram_posts"]],
                        "linkedin": [mcp_tools["web_data_linkedin_posts"]],
                        "youtube": [mcp_tools["web_data_youtube_videos"]],
                        "x": [mcp_tools["web_data_x_posts"]],
                        "web": [mcp_tools["scrape_as_markdown"]],
                    }

                    specialist_research_agent = Agent(
                        role=f"{platform.capitalize()} Specialist Research Agent",
                        goal=(
                            f"You are a {platform.capitalize()} deep content analysis/research specialist. "
                            f"Given one or more public {platform} URLs, your task is to extract high-signal facts, "
                            "insights, and key information from the content. "
                            "For each URL, return a strictly valid object (no extra attributes, no commentary) matching the output schema."
                        ),
                        backstory=(
                            "You operate with deep-research rigor and platform expertise. "
                            "Never speculate or infer beyond what is directly available. "
                            "Prioritize accuracy, clarity, and completeness in your extraction, and always adhere to the output schema."
                        ),
                        tools=tools_map[platform],
                        llm=self.specialist_llm,
                    )

                    # One task per URL to keep outputs atomic and typed
                    specialist_research_task = Task(
                        description=f"""
Process this {platform} URL: {urls}

Requirements:
- Use the provided tools to fetch content only.
- Summarize in bullet points ~500-750 words total (avoid fluff).
- Do not fabricate fields; leave unknowns out.

Output:
- Return ONLY valid JSON matching SpecialistOutput schema:
  {{ "platform": "{platform}", "url": "<canonical_url>", "summary": "<summary>", "metadata": {{...}} }}
""",
                        agent=specialist_research_agent,
                        output_pydantic=SpecialistOutput,
                        expected_output="Strict JSON for SpecialistOutput; no prose, no code fences.",
                    )

                    crew = Crew(
                        agents=[specialist_research_agent],
                        tasks=[specialist_research_task],
                        verbose=True,
                    )
                    # Use kickoff_async for parallel execution
                    print(f"DEBUG: Kickoff specialist crew for {platform}", flush=True)
                    platform_output: SpecialistOutput = await crew.kickoff_async()
                    print(f"DEBUG: Specialist crew for {platform} finished", flush=True)
                    return [platform_output]
            except Exception as e:
                print(f"DEBUG: Error in _process_platform for {platform}: {e}", flush=True)
                raise e

        # Process each platform bucket with clear failure isolation
        url_buckets_dict = (
            json.loads(inputs["urls_buckets"]["raw"])
            if isinstance(inputs["urls_buckets"]["raw"], str)
            else inputs["urls_buckets"]["raw"]
        )

        tasks = []
        platforms = []

        for platform, bucket in url_buckets_dict.items():
            tasks.append(_process_platform(platform, bucket))
            platforms.append(platform)

        # Run all tasks in parallel
        print(f"DEBUG: Dispatching {len(tasks)} platform tasks", flush=True)
        results_raw = await asyncio.gather(*tasks, return_exceptions=True)
        print("DEBUG: All platform tasks completed", flush=True)
        
        results: List[SpecialistOutput] = []
        
        for i, result in enumerate(results_raw):
            platform = platforms[i]
            if isinstance(result, Exception):
                print(f"DEBUG: {platform} specialist failed: {result}", flush=True)
                results.append(
                    SpecialistOutput(
                        platform=platform,
                        url="https://invalid.local",
                        summary=f"Error: {type(result).__name__}",
                        metadata={"detail": str(result)},
                    )
                )
            else:
                # result is List[SpecialistOutput]
                results.extend(result)

        return {"specialist_results": results}

    @listen(dispatch_to_specialists)
    def synthesize_response(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Final deep research response synthesis."""
        response_agent = Agent(
            role="Deep Research Synthesis Specialist",
            goal=(
                "Synthesize comprehensive research findings into a clear, engaging, and informative response "
                "that answers the user's query with depth and accuracy. Present findings in a structured, "
                "easy-to-read format similar to ChatGPT's deep research mode."
            ),
            backstory=(
                "You are an expert research analyst with deep expertise in synthesizing complex information "
                "from multiple sources. You excel at creating comprehensive, well-structured responses that "
                "provide users with actionable insights while maintaining clarity and engagement."
            ),
            llm=self.response_llm,
        )

        response_task = Task(
            description=f"""
Original Query: "{self.state.query}"

Research Context:
{inputs["specialist_results"]}

Your Task:
Create a comprehensive, well-structured markdown response that:

1. **Directly answers the user's query** with clear, actionable insights
2. **Synthesizes findings** from all available sources into coherent themes
3. **Provides specific details** with supporting evidence from sources
4. **Uses clear headings** and bullet points for easy scanning
5. **Includes source links** where applicable for credibility
6. **Highlights key takeaways** and important implications
7. **Maintains an engaging tone** while being informative

Structure your response with:
- Executive Summary (2-3 key points)
- Detailed Findings (organized by topic/theme)
- Key Insights & Implications
- Sources & References

Make it comprehensive yet readable, similar to high-quality research reports or ChatGPT's or Gemini's deep research mode.
""",
            expected_output="Comprehensive markdown response with clear structure, detailed findings, and source references.",
            agent=response_agent,
            markdown=True,
        )

        crew = Crew(agents=[response_agent], tasks=[response_task], verbose=True)
        final_md: str = crew.kickoff()
        self.state.final_response = str(final_md)
        return {"result": self.state.final_response}


# Usage example
async def main():
    flow = DeepResearchFlow()
    flow.state.query = "What is the latest update on iphone 17 launch?"
    result = await flow.kickoff_async()

    print(f"\n{'='*50}")
    print(f"FINAL RESULT")
    print(f"{'='*50}")
    print(result["result"])


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

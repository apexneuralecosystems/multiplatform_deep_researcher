"""
Deep Research Flow - CrewAI-based research workflow.
Orchestrates multi-platform research using MCP tools.
"""

import asyncio
import json
import logging
import traceback
from typing import Any, Dict, List

from crewai import Agent, Crew, LLM, Task
from crewai.flow.flow import Flow, listen, start
from crewai_tools import MCPServerAdapter
from pydantic import HttpUrl

from backend.core.config import settings
from backend.core.mcp import get_server_params
from backend.core.schemas import (
    DeepResearchFlowState,
    Platform,
    SpecialistOutput,
    URLBuckets,
)


class DeepResearchFlow(Flow[DeepResearchFlowState]):
    """
    Deep Research Flow using CrewAI.
    
    Orchestrates a multi-step research workflow:
    1. Search for relevant URLs across platforms
    2. Dispatch to platform specialists for content extraction
    3. Synthesize findings into a comprehensive response
    """
    
    # LLM configurations
    search_llm: Any = LLM(
        model=settings.SEARCH_MODEL,
        temperature=settings.SEARCH_TEMPERATURE,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )
    specialist_llm: Any = LLM(
        model=settings.SPECIALIST_MODEL,
        temperature=settings.SPECIALIST_TEMPERATURE,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )
    response_llm: Any = LLM(
        model=settings.RESPONSE_MODEL,
        temperature=settings.RESPONSE_TEMPERATURE,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )

    @start()
    def start_flow(self) -> Dict[str, Any]:
        """Start the flow by setting the query in the state."""
        return {"query": self.state.query}

    @listen(start_flow)
    def collect_urls(self) -> Dict[str, Any]:
        """Search web for user query and return URLBuckets object."""
        logging.info(f"Starting URL collection for query: {self.state.query}")
        try:
            params = get_server_params()
            
            if params is None:
                raise RuntimeError("MCP server params not configured. Check BRIGHT_DATA_API_TOKEN.")
            
            with MCPServerAdapter(params, trust_remote_code=True) as mcp_tools:
                logging.info(f"MCP tools available: {list(mcp_tools.keys()) if hasattr(mcp_tools, 'keys') else 'connected'}")
                
                search_agent = Agent(
                    role="Multiplatform Web Discovery Specialist",
                    goal=(
                        "Your objective is to identify and return a well-organized JSON object "
                        "containing only public, directly relevant links for a given user query. "
                        "The links should be grouped by platform: Instagram, LinkedIn, YouTube, "
                        "X (formerly Twitter), and the open web."
                    ),
                    backstory=(
                        "You are an expert web researcher skilled in using advanced search operators "
                        "and platform-specific techniques. You rigorously verify that every link is "
                        "public, accessible, and highly relevant to the query. You never include "
                        "duplicates or irrelevant results, and you never fabricate information."
                    ),
                    tools=[mcp_tools["search_engine"]],
                    llm=self.search_llm,
                )

                search_task = Task(
                    description=f'''
Query: "{self.state.query}"

Return JSON with these exact keys: ["instagram","linkedin","youtube","x","web"]
Each key has a list of max 1 URL (the most relevant one).
Empty list [] if no relevant result for that platform.

Rules:
- instagram: instagram.com URLs only
- linkedin: linkedin.com URLs only  
- youtube: youtube.com URLs only
- x: x.com or twitter.com URLs only
- web: article/blog URLs only

Output: Pure JSON, no markdown, no explanation.
''',
                    agent=search_agent,
                    output_pydantic=URLBuckets,
                    expected_output="JSON matching URLBuckets schema.",
                )

                crew = Crew(agents=[search_agent], tasks=[search_task], verbose=True)
                logging.info("Starting search crew...")
                out: URLBuckets = crew.kickoff()
                logging.info(f"Search complete. URLs found: {out}")
                return {"urls_buckets": out.model_dump(mode="raw")}

        except Exception as e:
            logging.error(f"collect_urls failed: {type(e).__name__}: {e}")
            logging.error(traceback.format_exc())
            empty = URLBuckets().model_dump(mode="raw")
            return {"urls_buckets": empty, "error": f"{e}"}

    @listen(collect_urls)
    async def dispatch_to_specialists(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Fan-out to platform specialists. Each platform is processed in parallel."""
        logging.info("Starting specialist dispatch...")
        
        async def _process_platform(
            platform: Platform, urls: List[HttpUrl]
        ) -> List[SpecialistOutput]:
            """Process a single platform bucket."""
            if not urls:
                logging.debug(f"Skipping {platform} - no URLs")
                return []

            try:
                params = get_server_params()
                
                if params is None:
                    raise RuntimeError("MCP server params not configured.")
                
                logging.info(f"Processing {platform} with {len(urls)} URLs...")
                
                with MCPServerAdapter(params, trust_remote_code=True) as mcp_tools:
                    tools_map: Dict[str, List[Any]] = {
                        "instagram": [mcp_tools["web_data_instagram_posts"]],
                        "linkedin": [mcp_tools["web_data_linkedin_posts"]],
                        "youtube": [mcp_tools["web_data_youtube_videos"]],
                        "x": [mcp_tools["web_data_x_posts"]],
                        "web": [mcp_tools["scrape_as_markdown"]],
                    }

                    specialist_agent = Agent(
                        role=f"{platform.capitalize()} Specialist Research Agent",
                        goal=(
                            f"You are a {platform.capitalize()} deep content analysis specialist. "
                            f"Given one or more public {platform} URLs, extract high-signal facts, "
                            "insights, and key information from the content."
                        ),
                        backstory=(
                            "You operate with deep-research rigor and platform expertise. "
                            "Never speculate or infer beyond what is directly available."
                        ),
                        tools=tools_map[platform],
                        llm=self.specialist_llm,
                    )

                    specialist_task = Task(
                        description=f'''
Fetch and summarize: {urls}

Output JSON with:
- platform: "{platform}"
- url: the URL processed
- summary: Key findings in 3-5 bullet points (max 200 words)
- metadata: {{}}
''',
                        agent=specialist_agent,
                        output_pydantic=SpecialistOutput,
                        expected_output="JSON matching SpecialistOutput schema.",
                    )

                    crew = Crew(
                        agents=[specialist_agent],
                        tasks=[specialist_task],
                        verbose=True,
                    )
                    platform_output: SpecialistOutput = await crew.kickoff_async()
                    logging.info(f"{platform} specialist complete")
                    return [platform_output]
                    
            except Exception as e:
                logging.error(f"Error in _process_platform for {platform}: {e}")
                raise e

        # Parse URL buckets data
        url_buckets_data = inputs.get("urls_buckets", {})
        
        if hasattr(url_buckets_data, 'raw'):
            url_buckets_dict = json.loads(url_buckets_data.raw) if isinstance(url_buckets_data.raw, str) else url_buckets_data.raw
        elif isinstance(url_buckets_data, str):
            url_buckets_dict = json.loads(url_buckets_data)
        elif isinstance(url_buckets_data, dict):
            url_buckets_dict = url_buckets_data
        else:
            url_buckets_dict = {"instagram": [], "linkedin": [], "youtube": [], "x": [], "web": []}

        # Process platforms in parallel
        tasks = []
        platforms = []

        for platform, bucket in url_buckets_dict.items():
            tasks.append(_process_platform(platform, bucket))
            platforms.append(platform)

        logging.info(f"Dispatching {len(tasks)} platform tasks...")
        results_raw = await asyncio.gather(*tasks, return_exceptions=True)
        
        results: List[SpecialistOutput] = []
        
        for i, result in enumerate(results_raw):
            platform = platforms[i]
            if isinstance(result, Exception):
                logging.error(f"{platform} specialist failed: {result}")
                results.append(
                    SpecialistOutput(
                        platform=platform,
                        url="https://invalid.local",
                        summary=f"Error: {type(result).__name__}",
                        metadata={"detail": str(result)},
                    )
                )
            else:
                results.extend(result)

        logging.info(f"All specialists complete. {len(results)} results collected.")
        return {"specialist_results": results}

    @listen(dispatch_to_specialists)
    def synthesize_response(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Final deep research response synthesis."""
        logging.info("Starting response synthesis...")
        
        response_agent = Agent(
            role="Deep Research Synthesis Specialist",
            goal=(
                "Synthesize comprehensive research findings into a clear, engaging, "
                "and informative response that answers the user's query with depth and accuracy."
            ),
            backstory=(
                "You are an expert research analyst with deep expertise in synthesizing "
                "complex information from multiple sources."
            ),
            llm=self.response_llm,
        )

        response_task = Task(
            description=f'''
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
''',
            expected_output="Comprehensive markdown response with clear structure.",
            agent=response_agent,
            markdown=True,
        )

        crew = Crew(agents=[response_agent], tasks=[response_task], verbose=True)
        final_md: str = crew.kickoff()
        self.state.final_response = str(final_md)
        logging.info("Response synthesis complete")
        return {"result": self.state.final_response}

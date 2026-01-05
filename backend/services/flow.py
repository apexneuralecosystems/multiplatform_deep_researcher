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

from backend.services.session import session_manager

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
    async def collect_urls(self) -> Dict[str, Any]:
        """Search web for user query and return URLBuckets object."""
        if self.state.session_id:
            await session_manager.update_agent_status(self.state.session_id, "search", "running", "Searching for relevant URLs...")

        logging.info(f"Starting URL collection for query: {self.state.query}")
        try:
            params = get_server_params()
            
            if params is None:
                raise RuntimeError("MCP server params not configured. Check BRIGHT_DATA_API_TOKEN.")
            
            with MCPServerAdapter(params) as mcp_tools:
                # Verify search_engine tool exists by trying to access it
                try:
                    test_tool = mcp_tools["search_engine"]
                    logging.info("✅ search_engine tool is available")
                except (KeyError, AttributeError, TypeError) as e:
                    logging.error(f"❌ search_engine tool NOT FOUND in MCP tools!")
                    logging.error(f"Error accessing tool: {e}")
                    logging.error("Note: MCPServerAdapter may need time to initialize tools.")
                    # Try to continue anyway - the tool might still work
                    logging.warning("⚠️ Continuing despite tool check failure - tool may still be accessible")
                
                search_agent = Agent(
                    role="Multiplatform Web Discovery Specialist",
                    goal="Use search_engine tool to find real URLs for each platform. Return JSON with URLs found via tool calls only.",
                    backstory=(
                        "Expert web researcher. MUST use search_engine tool for every search. "
                        "NEVER fabricate URLs. Return empty list [] if no results found."
                    ),
                    tools=[mcp_tools["search_engine"]],
                    llm=self.search_llm,
                    allow_delegation=False,
                    verbose=True,
                )

                search_task = Task(
                    description=f'''
Query: "{self.state.query}"

MANDATORY: Call search_engine tool 5 times (once per platform), then return JSON.

Workflow:
1. search_engine(query="{self.state.query}" site:instagram.com) → extract best Instagram URL or []
2. search_engine(query="{self.state.query}" site:linkedin.com) → extract best LinkedIn URL or []
3. search_engine(query="{self.state.query}" site:youtube.com) → extract best YouTube URL or []
4. search_engine(query="{self.state.query}" site:x.com) → extract best X/Twitter URL or []
5. search_engine(query="{self.state.query}") → extract best web article URL or []

Return JSON: {{"instagram":["url"],"linkedin":["url"],"youtube":["url"],"x":["url"],"web":["url"]}}
Each platform: max 1 URL from tool results, or empty list [].
IMPORTANT: Extract only the URL from tool responses. Ignore images, descriptions, and other data.
''',
                    agent=search_agent,
                    output_pydantic=URLBuckets,
                    expected_output="JSON matching URLBuckets schema with real URLs from search_engine tool.",
                    max_iter=7,  # Reduced from 10 to prevent context overflow (5 tool calls + 2 buffer)
                )

                crew = Crew(agents=[search_agent], tasks=[search_task], verbose=True)
                
                # Debug crew configuration
                logging.info("=" * 80)
                logging.info("SEARCH CREW CONFIGURATION:")
                logging.info(f"  Agent: {search_agent.role}")
                logging.info(f"  Tools available: {[tool.name if hasattr(tool, 'name') else str(tool) for tool in search_agent.tools]}")
                logging.info(f"  Task description length: {len(search_task.description)} chars")
                logging.info("=" * 80)
                
                logging.info("Starting search crew...")
                logging.info(f"Search query: {self.state.query}")
                
                try:
                    out: URLBuckets = crew.kickoff()
                    logging.info(f"Search complete. Raw output type: {type(out)}")
                    logging.info(f"Search complete. Raw output: {out}")
                    
                    # Handle case where CrewAI returns a string or dict instead of URLBuckets
                    if isinstance(out, str):
                        logging.warning("⚠️ CrewAI returned string instead of URLBuckets. Attempting to parse...")
                        try:
                            # Try to parse as JSON
                            parsed = json.loads(out)
                            out = URLBuckets(**parsed)
                            logging.info("✅ Successfully parsed string output to URLBuckets")
                        except (json.JSONDecodeError, TypeError) as e:
                            logging.error(f"Failed to parse string output: {e}")
                            logging.error(f"Raw string content: {out[:500]}")  # First 500 chars
                            out = URLBuckets()  # Fallback to empty
                    elif isinstance(out, dict):
                        logging.warning("⚠️ CrewAI returned dict instead of URLBuckets. Converting...")
                        try:
                            out = URLBuckets(**out)
                            logging.info("✅ Successfully converted dict to URLBuckets")
                        except Exception as e:
                            logging.error(f"Failed to convert dict to URLBuckets: {e}")
                            logging.error(f"Dict content: {out}")
                            out = URLBuckets()  # Fallback to empty
                    elif not isinstance(out, URLBuckets):
                        logging.warning(f"⚠️ Unexpected output type: {type(out)}. Creating empty URLBuckets.")
                        out = URLBuckets()
                    
                    logging.info(f"Final URLBuckets object: {out}")
                    logging.info(f"Final URLBuckets dict: {out.model_dump()}")
                    
                    # Count total URLs found
                    total_found = sum(len(urls) for urls in out.model_dump().values())
                    logging.info(f"Total URLs found across all platforms: {total_found}")
                    
                    if total_found == 0:
                        logging.warning("⚠️ SEARCH AGENT RETURNED NO URLs!")
                        logging.warning("This may indicate:")
                        logging.warning("  1. Search agent did not use search_engine tool")
                        logging.warning("  2. Search_engine tool returned no results")
                        logging.warning("  3. Search queries were too specific or no matching content exists")
                        logging.warning("  4. Agent output format was not recognized")
                        
                        # Log the raw output for debugging
                        logging.warning(f"Raw output for debugging: {repr(out)}")
                    
                    # Validate URLs are not obviously fake
                    for platform, urls in out.model_dump().items():
                        if urls:
                            logging.info(f"Platform {platform} has {len(urls)} URL(s)")
                            for url in urls:
                                if url and url != "https://invalid.local":
                                    # Basic validation - check if URL looks real
                                    if not (url.startswith("http://") or url.startswith("https://")):
                                        logging.warning(f"Invalid URL format for {platform}: {url}")
                                    elif "example.com" in url or "test.com" in url or "placeholder" in url.lower():
                                        logging.warning(f"Suspicious URL for {platform}: {url}")
                                    else:
                                        logging.info(f"✅ Validated URL for {platform}: {url}")
                        else:
                            logging.debug(f"No URLs found for {platform}")
                            
                except Exception as e:
                    logging.error(f"Error during search crew execution: {type(e).__name__}: {e}")
                    logging.error(traceback.format_exc())
                    # Return empty URLBuckets on error
                    out = URLBuckets()
                    logging.warning("Returning empty URLBuckets due to search error")
                
                if self.state.session_id:
                     await session_manager.update_agent_status(self.state.session_id, "search", "done", "URLs collected.")

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
            
            logging.info(f"Processing {platform} with URLs: {urls}")

            try:
                params = get_server_params()
                
                if params is None:
                    raise RuntimeError("MCP server params not configured.")
                
                logging.info(f"Processing {platform} with {len(urls)} URLs...")
                
                if self.state.session_id:
                    await session_manager.update_agent_status(
                        self.state.session_id, 
                        platform, 
                        "running", 
                        f"Analyzing {len(urls)} URLs..."
                    )
                
                with MCPServerAdapter(params) as mcp_tools:
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
You are given the following URL(s) to analyze: {urls}

CRITICAL: You MUST use the URL(s) provided above. Do NOT make up or guess URLs.

For each URL provided:
1. Use the appropriate tool to fetch and analyze the content
2. Extract key information and insights
3. Return the EXACT URL that was processed

Output JSON with:
- platform: "{platform}" (must match exactly)
- url: "{urls[0] if urls else 'N/A'}" (MUST be the exact URL from the input above)
- summary: Key findings in 3-5 bullet points (max 200 words)
- metadata: {{}}

IMPORTANT: The "url" field MUST be one of the URLs provided in the input above: {urls}
''',
                        agent=specialist_agent,
                        output_pydantic=SpecialistOutput,
                        expected_output="JSON matching SpecialistOutput schema with the exact URL from input.",
                    )

                    crew = Crew(
                        agents=[specialist_agent],
                        tasks=[specialist_task],
                        verbose=True,
                    )
                    platform_output: SpecialistOutput = await crew.kickoff_async()
                    logging.info(f"{platform} specialist complete")
                    
                    if self.state.session_id:
                        await session_manager.update_agent_status(
                            self.state.session_id, 
                            platform, 
                            "done", 
                            "Analysis complete."
                        )
                    
                    return [platform_output]
                    
            except Exception as e:
                logging.error(f"Error in _process_platform for {platform}: {e}")
                raise e

        # Parse URL buckets data
        logging.info(f"Dispatch input keys: {inputs.keys()}")
        url_buckets_data = inputs.get("urls_buckets", {})
        logging.info(f"URL buckets raw type: {type(url_buckets_data)}")
        logging.info(f"URL buckets raw value: {url_buckets_data}")
        
        if hasattr(url_buckets_data, 'raw'):
            url_buckets_dict = json.loads(url_buckets_data.raw) if isinstance(url_buckets_data.raw, str) else url_buckets_data.raw
        elif isinstance(url_buckets_data, str):
            url_buckets_dict = json.loads(url_buckets_data)
        elif isinstance(url_buckets_data, dict):
            url_buckets_dict = url_buckets_data
        else:
            url_buckets_dict = {"instagram": [], "linkedin": [], "youtube": [], "x": [], "web": []}
            
        logging.info(f"Parsed URL buckets dict: {url_buckets_dict}")

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
        
        # Log summary of results
        successful_results = []
        for r in results:
            if isinstance(r, dict):
                if r.get('url') and r.get('url') != "https://invalid.local":
                    successful_results.append(r)
            elif hasattr(r, 'url') and r.url != "https://invalid.local":
                successful_results.append(r)
        
        logging.info(f"Successful specialist results (with valid URLs): {len(successful_results)}")
        
        if len(successful_results) == 0 and len(results) > 0:
            logging.warning("⚠️ All specialist results have invalid URLs or errors!")
            for r in results:
                if isinstance(r, dict):
                    logging.warning(f"  - {r.get('platform', 'unknown')}: {r.get('url', 'no URL')} - {r.get('summary', 'no summary')[:50]}")
                elif hasattr(r, 'platform'):
                    logging.warning(f"  - {r.platform}: {r.url} - {r.summary[:50] if hasattr(r, 'summary') else 'no summary'}")
        elif len(successful_results) > 0:
            logging.info(f"✅ Found {len(successful_results)} valid URLs from specialists:")
            for r in successful_results:
                if isinstance(r, dict):
                    logging.info(f"  - {r.get('platform', 'unknown')}: {r.get('url', 'no URL')}")
                elif hasattr(r, 'platform'):
                    logging.info(f"  - {r.platform}: {r.url}")
        
        return {"specialist_results": results}

    @listen(dispatch_to_specialists)
    async def synthesize_response(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Final deep research response synthesis."""
        if self.state.session_id:
            await session_manager.update_agent_status(self.state.session_id, "synthesis", "running", "Synthesizing research report...")

        logging.info("Starting response synthesis...")
        
        # Extract URLs by platform from specialist results
        specialist_results = inputs.get("specialist_results", [])
        urls_by_platform = {
            "instagram": [],
            "linkedin": [],
            "youtube": [],
            "x": [],
            "web": []
        }
        
        # Handle both Pydantic models and dictionaries
        for result in specialist_results:
            # Check if it's a dictionary (serialized) or Pydantic model
            if isinstance(result, dict):
                platform = result.get("platform")
                url = result.get("url")
            elif hasattr(result, 'platform') and hasattr(result, 'url'):
                platform = result.platform
                url = result.url
            else:
                logging.warning(f"Unexpected result format: {type(result)}")
                continue
            
            if platform and platform in urls_by_platform and url and url != "https://invalid.local":
                urls_by_platform[platform].append(url)
                logging.info(f"Added URL for {platform}: {url}")
        
        # Log extracted URLs for debugging
        logging.info(f"Extracted URLs by platform: {urls_by_platform}")
        total_urls = sum(len(urls) for urls in urls_by_platform.values())
        logging.info(f"Total URLs extracted: {total_urls}")
        
        if total_urls == 0:
            logging.warning("⚠️ NO URLs FOUND in specialist results! This may indicate:")
            logging.warning("  1. Search agent didn't find any URLs")
            logging.warning("  2. Specialist agents failed to extract URLs")
            logging.warning("  3. URLs were filtered out during extraction")
        
        # Format URLs for the prompt
        urls_section = "\n\n## Source URLs by Platform:\n"
        has_any_urls = False
        for platform, urls in urls_by_platform.items():
            if urls:
                has_any_urls = True
                urls_section += f"\n### {platform.capitalize()}:\n"
                for url in urls:
                    urls_section += f"- {url}\n"
        
        if not has_any_urls:
            urls_section += "\n(No URLs were found from any platform.)\n"
            logging.warning("No URLs were extracted from specialist results!")
        
        # Format specialist results for better context
        formatted_results = []
        for r in specialist_results:
            if isinstance(r, dict):
                formatted_results.append({
                    "platform": r.get("platform", "unknown"),
                    "url": r.get("url", ""),
                    "summary": r.get("summary", "")
                })
            elif hasattr(r, 'platform') and hasattr(r, 'url') and hasattr(r, 'summary'):
                formatted_results.append({
                    "platform": r.platform,
                    "url": r.url,
                    "summary": r.summary
                })
            else:
                formatted_results.append(str(r))
        
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

Research Context from All Platforms:
{json.dumps(formatted_results, indent=2)}

{urls_section}

NOTE: If the "Source URLs by Platform" section above shows "(No URLs were found from any platform.)" or is empty, 
DO NOT include a "Source Links by Platform" section in your response at all. Simply omit that entire section.

Your Task:
Create a comprehensive, well-structured markdown response that:

1. **Directly answers the user's query** with clear, actionable insights
2. **Synthesizes findings** from all available sources into coherent themes
3. **Provides specific details** with supporting evidence from sources
4. **Uses clear headings** and bullet points for easy scanning
5. **MUST include all source URLs** organized by platform in a dedicated section
6. **Highlights key takeaways** and important implications
7. **Maintains an engaging tone** while being informative

Structure your response with:
- **Executive Summary** (2-3 key points)
- **Detailed Findings** (organized by topic/theme, with inline citations to sources)
- **Key Insights & Implications**
- **Source Links by Platform** (ONLY include if URLs are present in "Source URLs by Platform" section above):
  
  **CRITICAL**: If the "Source URLs by Platform" section above contains URLs, you MUST copy ALL of them and include them in your response. 
  Format each URL as a clickable markdown link: [Platform Name](URL)
  
  For each platform that has URLs listed above, create a subsection like:
  ### Instagram Sources:
  - [Link Description](URL)
  
  If the "Source URLs by Platform" section shows "(No URLs were found from any platform.)" or is empty, 
  DO NOT create a "Source Links by Platform" section at all - completely omit it from your response.

IMPORTANT: 
- Copy URLs EXACTLY as shown in the "Source URLs by Platform" section above
- Format URLs as clickable markdown links: [Platform Name - Brief Description](URL)
- Group URLs by their platform
- If a platform has no URLs in the section above, DO NOT include that platform section
- Use emojis or icons to make the output more engaging (🔗 for links, 📊 for data, etc.)
''',
            expected_output="Comprehensive markdown response with clear structure and all source URLs copied from the provided section.",
            agent=response_agent,
            markdown=True,
        )

        crew = Crew(agents=[response_agent], tasks=[response_task], verbose=True)
        final_md: str = crew.kickoff()
        self.state.final_response = str(final_md)
        logging.info("Response synthesis complete")
        return {"result": self.state.final_response}

"""
Jobs Parser Agent - Agentic implementation to parse job details from a webpage or text file
"""

import json
import logging
import dotenv
from typing import AsyncGenerator
from typing_extensions import override

from google.genai import types

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.invocation_context import InvocationContext
# from google.adk.tools import google_search
from google.adk.events import Event
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
# from google.genai import types

from src.utils.file_utils import load_config
# Import prompts to keep this file cleaner
from src.prompts.job_parsr_prompts import (
    bulk_text_parser_prompt,
)
# --- Initial Setup -----------------------------------------------------------
# Load environment variables and YAML configuration
dotenv.load_dotenv()
# Load agent/app config (models, agent settings)
agent_config = load_config("config/job_app_agent_config.yaml")
# Load job search parameters (keywords, locations, etc.)
search_config = load_config("config/jobsearch_config.yaml")

logger = logging.getLogger(__name__)
logger.setLevel(agent_config.get("logging_level", logging.INFO))

# --- Pipeline Constants ------------------------------------------------------
APP_NAME: str = agent_config.get("app_name", "JobParsr")
USER_ID: str = agent_config.get("user_id", "user_01")
SESSION_ID: str = agent_config.get("session_id", "session_01")
MAX_LOOP_ITERATIONS: int = agent_config.get("max_loop_iterations", 5)


# --- Agent Definitions -------------------------------------------------------
class JobParsr(BaseAgent):
    """
    Core orchestrator agent for the JobParsr pipeline.
    This agent coordinates the flow of information between sub-agents
    and manages the overall process of job details parsing.

    If a job posting is provided as a
    json file, it will be returned intact without any changes.

    If a job posting is provided as a text file, it will be parsed for all
    the keys requested and returned as a json object.

    If a job posting is provided as a webpage, the sub-agents will decide
    to scrape or use selenium (function tools) to extract the bulk data and
    fill all the keys requested and returned as a json object.
    """

    # Declare agent fields so Pydantic accepts assignments
    parseBulkText: LlmAgent

    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        name: str,
        parseBulkText: LlmAgent,
    ):
        super().__init__(
            name=name,
            parseBulkText=parseBulkText,
            sub_agents=[parseBulkText],
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        logger.info(f"[{self.name}] Starting Job Parsing Agent...")

        async for event in self.parseBulkText.run_async(ctx):
            yield event
        if event.error_message:
            logger.error(
                f"[{self.name}] Error in bulk text parsing: {event.error_message}"
            )
            return
        logger.info(
            f"[{self.name}] Bulk text parsing result: {event.content.parts[0].text}"
        )
        parsed_data = ctx.session.state.get("parsed_data")
        yield Event(
                content=types.Content(
                    role="assistant",
                    parts=[types.Part(text=json.dumps(parsed_data, indent=2))],
                ),
                author=self.name,
                )
        logger.info(f"[{self.name}] Job Parsing Agent completed successfully.")

# --- LlmAgent Instantiation --------------------------------------------------

safety_settings = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.OFF,
    ),
]
generate_content_config = types.GenerateContentConfig(
    safety_settings=safety_settings,
    temperature=0.28,  # TODO: use config file
    max_output_tokens=1000,  # TODO: use config file
    top_p=0.95,  # TODO: use config file
)

parseBulkText = LlmAgent(
    name="parseBulkText",
    model=(
        agent_config["models"]["gemini_2.5_flash"]
        if "gemini" in agent_config.get("parseBulkText_model")
        else LiteLlm(
            model=agent_config["models"][agent_config.get("parseBulkText_model")]
        )
    ),
    instruction=bulk_text_parser_prompt,
    input_schema=None,
    output_key="parsed_data",
    # generate_content_config=generate_content_config
)
# --- Agent Functions --------------------------------------------------------
def call_job_parsr_agent(job_posting: str) -> str:
    """
    Call the JobParsr agent with the provided job posting.

    Args:
        job_posting (str): The job posting to be parsed.    Returns:
        str: The parsed job details as a JSON-formatted string.
    """
    import uuid
    from datetime import datetime

    # Generate unique session ID for each request to avoid state conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_session_id = f"{SESSION_ID}_{timestamp}_{str(uuid.uuid4())[:8]}"
    unique_user_id = f"{USER_ID}_{timestamp}_{str(uuid.uuid4())[:8]}"

    # Move agent/session/runner creation inside the function for thread safety
    root_agent = JobParsr(
        name=APP_NAME,
        parseBulkText=parseBulkText,
    )
    session_service = InMemorySessionService()
    _ = session_service.create_session(
        app_name=APP_NAME,
        user_id=unique_user_id,
        session_id=unique_session_id,
    )
    runner = Runner(
        agent=root_agent, app_name=APP_NAME, session_service=session_service
    )

    prompt = f"Job posting: {job_posting}"
    content = types.Content(role="user", parts=[types.Part(text=prompt)])
    
    print("🧩 Creating invocation context...")
    print("⏳ This may take a few minutes, please wait...")

    current_agent = ""
    final_text: str = ""
    for event in runner.run(
        user_id=unique_user_id, session_id=unique_session_id, new_message=content
    ):
        if hasattr(event, "author") and event.author != current_agent:
            current_agent = event.author
            if current_agent == "parseBulkText":
                print(f"🤖 {current_agent}: {event.content.parts[0].text}")
        # Only break if the root agent emits the final response
        if event.is_final_response() and event.author == APP_NAME and event.content:
            # get the final text from parsed bulk text
            final_text = json.loads(
                event.content.parts[0].text,
            )
            print("✅ Agent work completed successfully.")
            print(f"📄 Final output: {final_text}")
            break
        elif event.error_message:
            print(f"❌ Error: {event.error_message}")
            break
    return final_text

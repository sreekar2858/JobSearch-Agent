"""
Jobs Parser Agent - Agentic implementation to parse job details from a webpage or text file
"""
import json
import logging
import dotenv
from typing import AsyncGenerator
from typing_extensions import override

from google.genai import types

from google.adk.agents import BaseAgent, LlmAgent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.invocation_context import InvocationContext
from google.adk.tools import google_search
from google.adk.events import Event
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
# from google.genai import types

from src.utils.file_utils import load_config
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
    decidingParser: LlmAgent
    parseBulkText: LlmAgent
    verifyJson: LlmAgent
    validateJob: LlmAgent
    decidingScraper: LlmAgent

    verifyValidate: SequentialAgent
    parseVerifyValidate: SequentialAgent
    
    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        name: str,
        decidingParser: LlmAgent,
        parseBulkText: LlmAgent,
        verifyJson: LlmAgent,
        validateJob: LlmAgent,
        decidingScraper: LlmAgent
    ):
        verifyValidate = SequentialAgent(
            name="verifyValidate",
            sub_agents=[verifyJson, validateJob],
        )
        parseVerifyValidate = SequentialAgent(
            name="parseVerifyValidate",
            sub_agents=[parseBulkText, verifyValidate],
        )
        super().__init__(
            name=name,
            decidingParser=decidingParser,
            parseBulkText=parseBulkText,
            verifyJson=verifyJson,
            validateJob=validateJob,
            decidingScraper=decidingScraper,
            verifyValidate=verifyValidate,
            parseVerifyValidate=parseVerifyValidate,
            sub_agents=[decidingParser, parseVerifyValidate, decidingScraper],
        )

# WHAT_IS:get_function_responses()[0].response

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        logger.info(f"[{self.name}] Starting Job Parsing Agent...")

        # Step 1: Decide which parser to use (text file, json file, or webpage)
        async for event in self.decidingParser.run_async(ctx):
            yield event
        if event.error_message:
            logger.error(f"[{self.name}] Error in deciding parser: {event.error_message}")
            return
        logger.info(f"[{self.name}] Decided parser: {event.content.parts[0].text}")
        # ctx.set("parser_decision", event.content.parts[0].text)

        parser_decision = event.content.parts[0].text
        if "json" in parser_decision.lower():
            # Step 2: If JSON, validate the JSON structure
            async for event in self.verifyJson.run_async(ctx):
                yield event

            if event.error_message:
                logger.error(f"[{self.name}] Error in JSON validation: {event.error_message}")
                return

            logger.info(f"[{self.name}] JSON validation result: {event.content.parts[0].text}")
            # ctx.set("json_validation", event.content.parts[0].text)

            if "valid" in event.content.parts[0].text:
                # Step 3: If valid, run the validation job
                async for event in self.validateJob.run_async(ctx):
                    yield event
                if event.error_message:
                    logger.error(f"[{self.name}] Error in job validation: {event.error_message}")
                    return
                logger.info(f"[{self.name}] Job validation result: {event.content.parts[0].text}")
                # ctx.set("job_validation", event.content.parts[0].text)
                if "valid" in event.content.parts[0].text:
                    # Step 4: If valid, return the JSON data
                    parsed_data = ctx.session.state.get("parsed_data")
                    logger.info(f"[{self.name}] Returning valid JSON data.")
                    yield Event(content=types.Content(role='assistant',
                                parts=[types.Part(text=json.dumps(parsed_data, indent=2))]),
                                author=self.name)
                else:
                    logger.error(f"[{self.name}] Invalid JSON data.")
                    yield Event(error_message = "Invalid JSON data.", author=self.name)
                    return
            else:
                logger.error(f"[{self.name}] Invalid JSON data.")
                yield Event(error_message = "Invalid JSON data.", author=self.name)
                return
            
        elif "bulk_text" in parser_decision.lower():
            # Step 2: If bulk text, parse the text data
            async for event in self.parseBulkText.run_async(ctx):
                # save this reponse for later use
                yield event
            if event.error_message:
                logger.error(f"[{self.name}] Error in bulk text parsing: {event.error_message}")
                return
            logger.info(f"[{self.name}] Bulk text parsing result: {event.content.parts[0].text}")
            # ctx.set("parsed_data", event.content.parts[0].text)
            # Step 3: Validate the parsed data
            async for event in self.verifyJson.run_async(ctx):
                yield event
            if event.error_message:
                logger.error(f"[{self.name}] Error in JSON validation: {event.error_message}")
                return
            logger.info(f"[{self.name}] JSON validation result: {event.content.parts[0].text}")
            # ctx.set("json_validation", event.content.parts[0].text)
            if "valid" in event.content.parts[0].text:
                # Step 4: If valid, run the validation job
                async for event in self.validateJob.run_async(ctx):
                    yield event
                if event.error_message:
                    logger.error(f"[{self.name}] Error in job validation: {event.error_message}")
                    return
                logger.info(f"[{self.name}] Job validation result: {event.content.parts[0].text}")
                # ctx.set("job_validation", event.content.parts[0].text)
                if "valid" in event.content.parts[0].text:
                    # Step 5: If valid, return the parsed data as JSON
                    parsed_data = ctx.session.state.get("parsed_data")
                    logger.info(f"[{self.name}] Returning valid parsed data.")
                    yield Event(content=types.Content(role='assistant',
                                parts=[types.Part(text=json.dumps(parsed_data, indent=2))]),
                                author=self.name)
                else:
                    logger.error(f"[{self.name}] Invalid parsed data.")
                    yield Event(error_message = "Invalid parsed data.", author=self.name)
                    return
            else:
                logger.error(f"[{self.name}] Invalid parsed data.")
                yield Event(error_message = "Invalid parsed data.", author=self.name)
                return

        elif "webpage" in parser_decision.lower():
            # Step 2: If webpage, decide whether to scrape or use Selenium
            async for event in self.decidingScraper.run_async(ctx):
                yield event

            if event.error_message:
                logger.error(f"[{self.name}] Error in deciding scraper: {event.error_message}")
                return

            logger.info(f"[{self.name}] Decided scraper: {event.content.parts[0].text}")
            # ctx.set("scraper_decision", event.content.parts[0].text)

            scraper_decision = event.content.parts[0].text
            if scraper_decision == "scrape":
                # TODO: Implement scraping logic
                logger.info(f"[{self.name}] Scraping logic not implemented yet.")
            elif scraper_decision == "selenium":
                # TODO: Implement Selenium logic
                logger.info(f"[{self.name}] Selenium logic not implemented yet.")
        else:
            logger.error(f"[{self.name}] Invalid parser decision: {parser_decision}")
            yield Event(error_message = "Invalid parser decision.", author=self.name)
            return
        logger.info(f"[{self.name}] Job Parsing Agent completed successfully.")
        
# Import prompts to keep this file cleaner
from src.prompts.job_parsr_prompts import (  # noqa: E402
    decide_parser_prompt,
    json_verify_prompt,
    json_validation_prompt,
    bulk_text_parser_prompt,
    webpage_parser_prompt,
)

# --- LlmAgent Instantiation --------------------------------------------------

safety_settings = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.OFF,
    ),
]
generate_content_config = types.GenerateContentConfig(
   safety_settings=safety_settings,
   temperature=0.28, #TODO: use config file
   max_output_tokens=1000, #TODO: use config file
   top_p=0.95, #TODO: use config file
)

decidingParser = LlmAgent(
    name="decidingParser",
    model=(agent_config['models']['gemini_2.5_flash'] 
            if 'gemini' in agent_config.get('decidingParser_model') 
            else LiteLlm(model=agent_config['models'][agent_config.get('decidingParser_model')])),
    instruction=decide_parser_prompt,
    input_schema=None,
    output_key="parser_decision",
    # generate_content_config=generate_content_config
)
parseBulkText = LlmAgent(
    name="parseBulkText",
    model=(agent_config['models']['gemini_2.5_flash'] 
            if 'gemini' in agent_config.get('parseBulkText_model') 
            else LiteLlm(model=agent_config['models'][agent_config.get('parseBulkText_model')])),
    instruction=bulk_text_parser_prompt,
    input_schema=None,
    output_key="parsed_data",
    # generate_content_config=generate_content_config
)
verifyJson = LlmAgent(
    name="verifyJson",
    model=(agent_config['models']['gemini_2.5_flash'] 
            if 'gemini' in agent_config.get('verifyJson_model') 
            else LiteLlm(model=agent_config['models'][agent_config.get('verifyJson_model')])),
    instruction=json_verify_prompt,
    input_schema=None,
    output_key="json_validation",
    # generate_content_config=generate_content_config
)
validateJob = LlmAgent(
    name="validateJob",
    model=(agent_config['models']['gemini_2.5_flash'] 
            if 'gemini' in agent_config.get('validateJob_model') 
            else LiteLlm(model=agent_config['models'][agent_config.get('validateJob_model')])),
    instruction=json_validation_prompt,
    input_schema=None,
    output_key="validation_result",
    tools=[google_search],
    # generate_content_config=generate_content_config
)
decidingScraper = LlmAgent(
    name="decidingScraper",
    model=(agent_config['models']['gemini_2.5_flash'] 
            if 'gemini' in agent_config.get('decidingScraper_model') 
            else LiteLlm(model=agent_config['models'][agent_config.get('decidingScraper_model')])),
    instruction=webpage_parser_prompt,
    input_schema=None,
    output_key="scraper_decision",
    # generate_content_config=generate_content_config
)

def call_job_parsr_agent(job_posting: str) -> str:
    """
    Call the JobParsr agent with the provided job posting.
    
    Args:
        job_posting (str): The job posting to be parsed.
    
    Returns:
        str: The parsed job details in JSON format.
    """

    # Move agent/session/runner creation inside the function for thread safety
    root_agent = JobParsr(
        name=APP_NAME,
        decidingParser=decidingParser,
        parseBulkText=parseBulkText,
        verifyJson=verifyJson,
        validateJob=validateJob,
        decidingScraper=decidingScraper,
    )
    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

    prompt = f"Job posting: {job_posting}"
    content = types.Content(role='user', parts=[types.Part(text=prompt)])

    print("🧩 Creating invocation context...")
    print("⏳ This may take a few minutes, please wait...")

    current_agent = ""
    final_text: str = ""
    for event in runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
        if hasattr(event, "author") and event.author != current_agent:
            current_agent = event.author
            if current_agent == "decidingParser":
                print(f"🤖 {current_agent}: {event.content.parts[0].text}")
            elif current_agent == "parseBulkText":
                print(f"🤖 {current_agent}: {event.content.parts[0].text}")
            elif current_agent == "verifyJson":
                print(f"🤖 {current_agent}: {event.content.parts[0].text}")
            elif current_agent == "validateJob":
                print(f"🤖 {current_agent}: {event.content.parts[0].text}")
            elif current_agent == "decidingScraper":
                print(f"🤖 {current_agent}: {event.content.parts[0].text}")
        # Only break if the root agent emits the final response
        if event.is_final_response() and event.author == APP_NAME and event.content:
            # get the final text from parsed bulk text
            final_text = json.loads(event.content.parts[0].text, )
            print("✅ Agent work completed successfully.")
            print(f"📄 Final output: {final_text}")
            break
        elif event.error_message:
            print(f"❌ Error: {event.error_message}")
            break
    return final_text

"""
Cover Letter Writer Agent - Main agent implementation for cover letter generation.

This module defines the cover letter generation pipeline, including:
- Initial draft generation
- Critique and revision loops
- Grammar checking
- Final draft preparation
"""
import json
import logging
import dotenv
from typing import AsyncGenerator, Tuple
from typing_extensions import override

from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from src.utils.file_utils import load_config, load_docx_template, load_text_file
from src.utils.exit_conditions import ExitConditionAgent

# Import prompts
from src.prompts.cover_letter_prompts import (
    initial_draft_prompt, 
    critic_prompt,
    fact_check_prompt,
    reviser_prompt,
    grammar_check_prompt,
    final_draft_prompt
)

# --- Initial Setup -----------------------------------------------------------
# Load environment variables and YAML configuration
dotenv.load_dotenv()
agent_config = load_config("config/cv_app_agent_config.yaml")  # We'll reuse the CV config
file_config = load_config("config/file_config.yaml")

# Validate and load Word template
coverletter_template_path: str = file_config['templates']['cover_letter']

logger = logging.getLogger(__name__)
logger.setLevel(agent_config.get("logging_level", logging.INFO))

# --- Pipeline Constants ------------------------------------------------------
APP_NAME: str = "CoverLetterWriter"
USER_ID: str = agent_config.get("user_id", "user_01")
SESSION_ID: str = agent_config.get("session_id", "session_02")  # Different from CV session
MAX_LOOP_ITERATIONS: int = agent_config.get("max_loop_iterations", 5)

# --- Agent Definitions -------------------------------------------------------
class CoverLetterWriter(BaseAgent):
    """
    Core orchestrator for the cover letter writing workflow. Sets up:
      - initial_draft: First pass generation agent
      - loop_agent: Repeated critique & revision
      - sequential_agent: Grammar check and final drafting

    Workflow:
      1. initial_draft → state['current_draft']
      2. loop_agent → state['current_draft'] updated
      3. sequential_agent → state['final_draft']

    Relies on InMemorySessionService for state persistence.
    """
    # Declare agent fields so Pydantic accepts assignments
    initial_draft: LlmAgent
    critic: LlmAgent
    fact_check: LlmAgent
    reviser: LlmAgent
    grammar_check: LlmAgent
    final_draft: LlmAgent
    loop_agent: LoopAgent
    sequential_agent: SequentialAgent
    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        name: str,
        initial_draft: LlmAgent,
        critic: LlmAgent,
        fact_check: LlmAgent,
        reviser: LlmAgent,
        grammar_check: LlmAgent,
        final_draft: LlmAgent,
    ):
        loop_agent = LoopAgent(
            name="CritiqueReviseLoop",
            sub_agents=[critic, fact_check, reviser, ExitConditionAgent()],
            max_iterations=MAX_LOOP_ITERATIONS
        )
        sequential_agent = SequentialAgent(
            name="PostProcessors",
            sub_agents=[grammar_check, final_draft],
        )
        super().__init__(
            name=name,
            initial_draft=initial_draft,
            critic=critic,
            fact_check=fact_check,
            reviser=reviser,
            grammar_check=grammar_check,
            final_draft=final_draft,
            loop_agent=loop_agent,
            sequential_agent=sequential_agent,
            sub_agents=[initial_draft, loop_agent, sequential_agent]
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        logger.info(f"[{self.name}] Starting cover letter pipeline...")

        # Step 1: Initial Draft
        async for event in self.initial_draft.run_async(ctx):
            logger.debug(f"InitialDraft → {event}")
            yield event
        if not ctx.session.state.get("current_draft"):
            logger.error("Initial draft missing, aborting pipeline.")
            return

        # Step 2: Critique & Revision Loop
        async for event in self.loop_agent.run_async(ctx):
            logger.debug(f"LoopAgent → {event}")
            yield event

        # Step 3: Grammar & Final Draft
        async for event in self.sequential_agent.run_async(ctx):
            logger.debug(f"SequentialAgent → {event}")
            yield event

        logger.info(f"[{self.name}] Pipeline complete. Final draft available.")

# --- LlmAgent Instantiation --------------------------------------------------
initial_draft = LlmAgent(
    name="InitialDraftGenerator",
    model=(agent_config['models']['gemini_2.5_flash'] 
            if 'gemini' in agent_config.get('initial_draft_model') 
            else LiteLlm(model=agent_config['models'][agent_config.get('initial_draft_model')])),
    instruction=initial_draft_prompt,
    input_schema=None,
    output_key="current_draft",
)

critic = LlmAgent(
    name="Critic",
    model=(agent_config['models']['gemini_2.5_flash'] 
            if 'gemini' in agent_config.get('critic_model') 
            else LiteLlm(model=agent_config['models'][agent_config.get('critic_model')])),
    instruction=critic_prompt,
    input_schema=None,
    output_key="critic_feedback",
)

fact_check = LlmAgent(
    name="FactChecker",
    model=(agent_config['models']['gemini_2.5_flash'] 
            if 'gemini' in agent_config.get('fact_check_model') 
            else LiteLlm(model=agent_config['models'][agent_config.get('fact_check_model')])),
    instruction=fact_check_prompt,
    input_schema=None,
    output_key="fact_check_report",
)

reviser = LlmAgent(
    name="Reviser",
    model=(agent_config['models']['gemini_2.5_flash'] 
            if 'gemini' in agent_config.get('reviser_model') 
            else LiteLlm(model=agent_config['models'][agent_config.get('reviser_model')])),
    instruction=reviser_prompt,
    input_schema=None,
    output_key="current_draft",
)

grammar_check = LlmAgent(
    name="GrammarChecker",
    model=(agent_config['models']['gemini_2.5_flash'] 
            if 'gemini' in agent_config.get('grammar_check_model') 
            else LiteLlm(model=agent_config['models'][agent_config.get('grammar_check_model')])),
    instruction=grammar_check_prompt,
    input_schema=None,
    output_key="grammar_corrections",
)

final_draft = LlmAgent(
    name="FinalDraftGenerator",
    model=(agent_config['models']['gemini_2.5_flash'] 
            if 'gemini' in agent_config.get('final_draft_model') 
            else LiteLlm(model=agent_config['models'][agent_config.get('final_draft_model')])),
    instruction=final_draft_prompt,
    input_schema=None,
    output_key="final_draft",
)

def call_cover_letter_agent(job_details: str) -> Tuple[str, str, str]:
    """
    1. Reload and validate the DOCX template.
    2. Construct a user prompt embedding `template_text` and `job_details`.
    3. Execute the agent workflow end-to-end.
    4. Map the final draft back into the Word document's paragraphs.
    5. Save the filled document and return paths along with state.
    """
    
    # --- Pipeline Assembly & Execution ------------------------------------------
    root_agent = CoverLetterWriter(
        name="CoverLetterWriter",
        initial_draft=initial_draft,
        critic=critic,
        fact_check=fact_check,
        reviser=reviser,
        grammar_check=grammar_check,
        final_draft=final_draft,
    )

    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

    print("🔄 Loading cover letter template...")
    if coverletter_template_path and coverletter_template_path.endswith('.docx'):
        doc, tmpl_text = load_docx_template(coverletter_template_path)
    elif coverletter_template_path and coverletter_template_path.endswith('.txt'):
        tmpl_text = load_text_file(coverletter_template_path) # dumps the bulk text into a string
    else:
        raise ValueError("Unsupported template format. Only .docx and .txt are supported.")

    prompt = f"TEMPLATE:\n{tmpl_text}\n\nJOB: {job_details}"  
    content = types.Content(role='user', parts=[types.Part(text=prompt)])

    print("🚀 Starting cover letter generation pipeline...")
    print("⏳ This may take a few minutes, please wait...")
    
    current_agent = ""
    events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)
    final_text: str = ""
    for evt in events:
        # Track which agent is currently working
        if hasattr(evt, 'author') and evt.author != current_agent:
            current_agent = evt.author
            if current_agent == "InitialDraftGenerator":
                print("📝 Generating initial cover letter draft...")
            elif current_agent == "Critic":
                print("🔍 Evaluating draft for improvements...")
            elif current_agent == "FactChecker":
                print("🧐 Validating factual accuracy...")
            elif current_agent == "Reviser":
                print("✏️ Implementing revisions...")
            elif current_agent == "ExitConditionChecker":
                print("🔄 Checking if revisions are complete...")
            elif current_agent == "GrammarChecker":
                print("🔤 Polishing grammar and style...")
            elif current_agent == "FinalDraftGenerator":
                print("✨ Finalizing cover letter content...")
        
        if evt.is_final_response() and evt.content:
            print("✅ Cover letter generation complete!")
            final_text = evt.content.parts[0].text
    
    print("📄 Applying content to cover letter template...")
    if coverletter_template_path.endswith('.docx'):
        # Inject lines into Word template
        lines = final_text.split("\n")
        for idx, paragraph in enumerate(doc.paragraphs):
            if idx < len(lines):
                paragraph.text = lines[idx]
        
        # Save the document to output folder
        output_path = f"output/custom_cover_letter.docx"
        doc.save(output_path)
        return final_text, json.dumps(session.state, indent=2), output_path

    elif coverletter_template_path.endswith('.txt'):
        # Save the text to output folder
        output_path = f"output/custom_cover_letter.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_text)
        return final_text, json.dumps(session.state, indent=2), output_path
    
    else:
        raise ValueError("Unsupported template format. Only .docx and .txt are supported.")

if __name__ == "__main__":
    # Example run
    query = "Data Scientist at TechCorp with expertise in machine learning and data visualization."
    cover_letter_text, state_json, doc_path = call_cover_letter_agent(query)
    print(cover_letter_text)
    logger.info(f"Final cover letter document saved to {doc_path}")
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
    final_draft_prompt,
)

# --- Initial Setup -----------------------------------------------------------
# Load environment variables and YAML configuration
dotenv.load_dotenv()
agent_config = load_config(
    "config/cv_app_agent_config.yaml"
)  # We'll reuse the CV config
file_config = load_config("config/file_config.yaml")

# Validate and load Word template
coverletter_template_path: str = file_config["templates"]["cover_letter"]

logger = logging.getLogger(__name__)
logger.setLevel(agent_config.get("logging_level", logging.INFO))

# --- Pipeline Constants ------------------------------------------------------
APP_NAME: str = "CoverLetterWriter"
USER_ID: str = agent_config.get("user_id", "user_01")
SESSION_ID: str = agent_config.get(
    "session_id", "session_02"
)  # Different from CV session
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
            max_iterations=MAX_LOOP_ITERATIONS,
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
            sub_agents=[initial_draft, loop_agent, sequential_agent],
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


# --- LlmAgent Factory Functions -----------------------------------------------
def create_initial_draft_agent():
    """Create a new initial draft agent for each request to avoid parent conflicts"""
    return LlmAgent(
        name="InitialDraftGenerator",
        model=(
            agent_config["models"]["gemini_2.5_flash"]
            if "gemini" in agent_config.get("initial_draft_model")
            else LiteLlm(
                model=agent_config["models"][agent_config.get("initial_draft_model")]
            )
        ),
        instruction=initial_draft_prompt,
        input_schema=None,
        output_key="current_draft",
    )


def create_critic_agent():
    """Create a new critic agent for each request to avoid parent conflicts"""
    return LlmAgent(
        name="Critic",
        model=(
            agent_config["models"]["gemini_2.5_flash"]
            if "gemini" in agent_config.get("critic_model")
            else LiteLlm(model=agent_config["models"][agent_config.get("critic_model")])
        ),
        instruction=critic_prompt,
        input_schema=None,
        output_key="critic_feedback",
    )


def create_fact_check_agent():
    """Create a new fact check agent for each request to avoid parent conflicts"""
    return LlmAgent(
        name="FactChecker",
        model=(
            agent_config["models"]["gemini_2.5_flash"]
            if "gemini" in agent_config.get("fact_check_model")
            else LiteLlm(
                model=agent_config["models"][agent_config.get("fact_check_model")]
            )
        ),
        instruction=fact_check_prompt,
        input_schema=None,
        output_key="fact_check_report",
    )


def create_reviser_agent():
    """Create a new reviser agent for each request to avoid parent conflicts"""
    return LlmAgent(
        name="Reviser",
        model=(
            agent_config["models"]["gemini_2.5_flash"]
            if "gemini" in agent_config.get("reviser_model")
            else LiteLlm(
                model=agent_config["models"][agent_config.get("reviser_model")]
            )
        ),
        instruction=reviser_prompt,
        input_schema=None,
        output_key="current_draft",
    )


def create_grammar_check_agent():
    """Create a new grammar check agent for each request to avoid parent conflicts"""
    return LlmAgent(
        name="GrammarChecker",
        model=(
            agent_config["models"]["gemini_2.5_flash"]
            if "gemini" in agent_config.get("grammar_check_model")
            else LiteLlm(
                model=agent_config["models"][agent_config.get("grammar_check_model")]
            )
        ),
        instruction=grammar_check_prompt,
        input_schema=None,
        output_key="grammar_corrections",
    )


def create_final_draft_agent():
    """Create a new final draft agent for each request to avoid parent conflicts"""
    return LlmAgent(
        name="FinalDraftGenerator",
        model=(
            agent_config["models"]["gemini_2.5_flash"]
            if "gemini" in agent_config.get("final_draft_model")
            else LiteLlm(
                model=agent_config["models"][agent_config.get("final_draft_model")]
            )
        ),
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

    try:
        # Create fresh agents for each request to avoid parent conflicts
        fresh_initial_draft = create_initial_draft_agent()
        fresh_critic = create_critic_agent()
        fresh_fact_check = create_fact_check_agent()
        fresh_reviser = create_reviser_agent()
        fresh_grammar_check = create_grammar_check_agent()
        fresh_final_draft = create_final_draft_agent()

        # --- Pipeline Assembly & Execution ------------------------------------------
        root_agent = CoverLetterWriter(
            name="CoverLetterWriter",
            initial_draft=fresh_initial_draft,
            critic=fresh_critic,
            fact_check=fresh_fact_check,
            reviser=fresh_reviser,
            grammar_check=fresh_grammar_check,
            final_draft=fresh_final_draft,
        )

        session_service = InMemorySessionService()

        # Generate unique session ID for each request to avoid state conflicts
        import uuid
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_session_id = f"{SESSION_ID}_{timestamp}_{str(uuid.uuid4())[:8]}"
        unique_user_id = f"{USER_ID}_{timestamp}_{str(uuid.uuid4())[:8]}"

        session = session_service.create_session(
            app_name=APP_NAME,
            user_id=unique_user_id,
            session_id=unique_session_id,
        )
        runner = Runner(
            agent=root_agent, app_name=APP_NAME, session_service=session_service
        )

        print("🔄 Loading cover letter template...")
        if coverletter_template_path and coverletter_template_path.endswith(".docx"):
            doc, tmpl_text = load_docx_template(coverletter_template_path)
        elif coverletter_template_path and coverletter_template_path.endswith(".txt"):
            tmpl_text = load_text_file(
                coverletter_template_path
            )  # dumps the bulk text into a string
        else:
            raise ValueError(
                "Unsupported template format. Only .docx and .txt are supported."
            )

        prompt = f"TEMPLATE:\n{tmpl_text}\n\nJOB: {job_details}"
        content = types.Content(role="user", parts=[types.Part(text=prompt)])

        print("🚀 Starting cover letter generation pipeline...")
        print("⏳ This may take a few minutes, please wait...")

        try:
            current_agent = ""
            events = runner.run(
                user_id=unique_user_id,
                session_id=unique_session_id,
                new_message=content,
            )
            final_text: str = ""
            for evt in events:
                # Track which agent is currently working
                if hasattr(evt, "author") and evt.author != current_agent:
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

            if not final_text:
                raise Exception("Failed to generate cover letter content")

            print("📄 Applying content to cover letter template...")
            if coverletter_template_path.endswith(".docx"):
                # Inject lines into Word template
                lines = final_text.split("\n")
                for idx, paragraph in enumerate(doc.paragraphs):
                    if idx < len(lines):
                        paragraph.text = lines[idx]
                return final_text, json.dumps(session.state, indent=2), doc

            elif coverletter_template_path.endswith(".txt"):
                return final_text, json.dumps(session.state, indent=2), final_text

            else:
                raise ValueError(
                    "Unsupported template format. Only .docx and .txt are supported."
                )

        except Exception as e:
            print(f"⚠️ Error during cover letter generation: {e}")
            print("⚠️ Falling back to simple cover letter generation...")
            return generate_simple_cover_letter(job_details, coverletter_template_path)

    except Exception as e:
        print(f"⚠️ Error setting up cover letter generation: {e}")
        print("⚠️ Falling back to simple cover letter generation...")
        return generate_simple_cover_letter(job_details, coverletter_template_path)


def generate_simple_cover_letter(
    job_details: str, template_path: str
) -> Tuple[str, str, str]:
    """
    A fallback function that generates a simple cover letter without using the complex agent system.
    This is used when the main agent system fails due to API issues.
    """
    print("🔄 Using fallback cover letter generation...")

    try:  # Parse job details
        job_data = json.loads(job_details)
        job_title = job_data.get("job_title", "Unknown Position")
        company = job_data.get("company_name", "Unknown Company")
        responsibilities = job_data.get("job_responsibilities", [])
        # Get requirements but we don't use them directly in this simple version
        skills = job_data.get("skills_required", [])

        # Create a simple cover letter
        today_date = "May 11, 2025"

        cover_letter = f"""
{today_date}

Dear Hiring Manager,

I am writing to express my interest in the {job_title} position at {company}. After reviewing the job description, I believe that my skills and experience align well with what you are seeking in a candidate.

With experience in {", ".join(skills[:3]) if skills else "areas relevant to this position"}, I am confident in my ability to contribute effectively to your team. I have successfully {"delivered projects requiring " + responsibilities[0] if responsibilities else "handled responsibilities similar to those described in the job posting"}.

What particularly interests me about {company} is your focus on {"innovation and development" if not responsibilities else responsibilities[0]}. I am eager to bring my expertise in {skills[0] if skills else "relevant areas"} to contribute to your continued success.

I look forward to the opportunity to discuss how my background, skills, and experiences would be a good match for this position. Thank you for your time and consideration.

Sincerely,
[Your Name]
[Your Contact Information]
        """

        # Return the simple cover letter
        state = {"simple_fallback": True}
        if template_path.endswith(".txt"):
            return cover_letter, json.dumps(state), cover_letter
        else:
            # For docx templates, we'd need more complex handling here
            # For now, just return the text
            return cover_letter, json.dumps(state), cover_letter

    except Exception as e:
        # If all else fails, return a very basic template
        print(f"⚠️ Error in fallback cover letter generation: {e}")
        basic_letter = "Cover Letter\n\nDear Hiring Manager,\n\nThis is a placeholder cover letter generated due to technical issues with the full cover letter generation system.\n\nPlease try again later or contact support.\n\nSincerely,\n[Your Name]"
        state = {"error": str(e)}
        return basic_letter, json.dumps(state), basic_letter


if __name__ == "__main__":
    # Example run
    query = "Data Scientist at TechCorp with expertise in machine learning and data visualization."
    cover_letter_text, state_json, doc_path = call_cover_letter_agent(query)
    print(cover_letter_text)
    logger.info(f"Final cover letter document saved to {doc_path}")

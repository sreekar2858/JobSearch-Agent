"""
Exit conditions for agent loops.

This module defines agents that can determine when to exit recursive loops,
such as when critique-revision cycles can be considered complete.
"""
from typing import AsyncGenerator
import logging
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.agents import BaseAgent

logger = logging.getLogger(__name__)

class ExitConditionAgent(BaseAgent):
    """
    Monitors the 'critic_feedback' in session state. Exits the review loop when
    feedback indicates completion. Criteria include:
      - Contains 'strongly approve'
      - Contains 'no further revisions needed'
      - Feedback explicitly declares 'complete'

    Attributes:
      name: str
      description: str
    """
    name: str = "ExitConditionChecker"
    description: str = "Detects when critique feedback meets exit criteria."

    async def _run_async_impl(
        self, context: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        feedback: str = context.session.state.get("critic_feedback", "").lower()
        exit_phrases = ["approve", "strongly approve", "no further revisions needed", "complete"]
        
        if any(phrase in feedback for phrase in exit_phrases):
            logger.info("[ExitConditionAgent] Exit condition met, escalating.")
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            logger.debug("[ExitConditionAgent] Exit conditions not met, continuing loop.")
"""Digital FTE Customer Success Agent Package"""

from .customer_success_agent import DigitalFTEAgent, create_agent_for_channel
from .prompts import get_system_prompt, should_escalate

__all__ = [
    'DigitalFTEAgent',
    'create_agent_for_channel',
    'get_system_prompt',
    'should_escalate'
]

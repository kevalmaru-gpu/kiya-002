from core.agent.stateless_agent_class import StatelessAgent
from tools.export_leads_to_doc import ExportLeadsToDocTool
import logging

logger = logging.getLogger(__name__)

LeadGenerationAgent = StatelessAgent(name="LeadGenerationAgent", instructions="You are a lead generation agent that can generate leads for a company by doing webscrapping.", llm_type="gemini", next_node=ExportLeadsToDocTool(), enable_web_search=True)

async def generate_leads_controller(prompt: str):
    logger.info(f"Generating leads with prompt: {prompt}")
    response = await LeadGenerationAgent.call(prompt)
    logger.info(f"Generated leads: {response}")
    return response
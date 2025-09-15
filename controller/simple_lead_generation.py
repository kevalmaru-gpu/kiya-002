from workflows.lead_generation_workflow import LeadGenerationWorkflow
import logging

logger = logging.getLogger(__name__)

async def generate_leads_controller(prompt: str):
    logger.info(f"Generating leads with prompt: {prompt}")
    response = await LeadGenerationWorkflow.run(prompt)
    logger.info(f"Generated leads: {response}")
    return response
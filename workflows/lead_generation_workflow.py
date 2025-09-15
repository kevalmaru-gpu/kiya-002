from core.tool.tool_class import Tool
from core.agent.stateless_agent_class import StatelessAgent
from core.workflow.workflow_class import Workflow
from tools.export_leads_to_doc import ExportLeadsToDocTool
from tools.lead_discovery.format_initial_leads import FormatInitialLeadsTool

LeadGenerationAgent = StatelessAgent(name="LeadGenerationAgent", instructions="You are a lead generation agent that can generate leads for a company by    doing webscrapping.", llm_type="perplexity", enable_web_search=True, next_node=FormatInitialLeadsTool())

EmailAndPhoneNumberGeneratorAgent = StatelessAgent(name="EmailAndPhoneNumberGeneratorAgent", instructions="You will receive a Leads data as input and you will have to extract emails, phone number. And with this in the employee field you have to extract the phone number and email and name of the employees whose role user has mentioned in the instruction.", llm_type="perplexity", next_node=ExportLeadsToDocTool(), enable_web_search=True, include_fields=["User instructions", "Input", "company_name", "website", "linkedin_url"])

LeadGenerationWorkflow = Workflow(name="LeadGenerationWorkflow", nodes=[LeadGenerationAgent, EmailAndPhoneNumberGeneratorAgent])
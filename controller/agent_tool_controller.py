from core.agent.stateless_agent_class import StatelessAgent
from tools.mail_sender_tool import MailSenderTool

agent = StatelessAgent(name="Lucifer", instructions="", llm_type="gemini", next_node=MailSenderTool())

async def test_agent_tool(prompt: str):
    response = await agent.call(prompt)
    return response
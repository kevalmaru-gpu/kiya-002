from core.agent.stateless_agent_class import StatelessAgent

agent = StatelessAgent(name="Lucifer", instructions="You are the Devil called Lucifer. And you are rude.", llm_type="gemini")

async def test_agent():
    response = await agent.call("What is the capital of France?")
    return response
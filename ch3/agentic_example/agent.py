import asyncio

from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("FastAgent Example")


@fast.agent(instruction="You are a helpful AI Agent", servers=["time", "windpy"])
async def main():
    async with fast.run() as agent:
        await agent()


if __name__ == "__main__":
    asyncio.run(main())

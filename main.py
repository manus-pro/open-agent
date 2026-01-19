import asyncio

from app.agent.manus import Manus
from app.logger import get_logger

logger = get_logger("open-agent")


async def main():
    agent = Manus()
    while True:
        try:
            prompt = input("Enter your prompt (or 'quit' to quit): ")
            if prompt.lower() == "quit":
                logger.info("Goodbye!")
                break
            logger.warning("Processing your request...")
            await agent.run(prompt)
        except KeyboardInterrupt:
            logger.warning("Goodbye!")
            break


if __name__ == "__main__":
    asyncio.run(main()) 
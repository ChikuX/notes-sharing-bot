import asyncio
import sys
import logging

from src.core.bot import bot, app
from src.handlers import register_handlers
from src.services import db_service


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    # Initialize database connection pool & create tables
    await db_service.connect_db()

    # Register all handler routers
    register_handlers(app)

    try:
        logging.info("Bot starting...")
        await app.start_polling(bot)
    finally:
        await db_service.close_db()


if __name__ == "__main__":
    asyncio.run(main())
"""
Telegram bot entry point.

Run with: python -m src.bot.app
Requires BOT_TOKEN environment variable.
"""
import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.persistence.sqlite_repo import SQLiteRepository
from src.domain.services import OrderService, DebtService, PaymentService
from .handlers import create_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_bot_token() -> str:
    """
    Get bot token from environment.

    Raises:
        SystemExit: If BOT_TOKEN is not set
    """
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("BOT_TOKEN environment variable is not set")
        sys.exit(1)
    return token


def create_services(db_path: str = "debts.db"):
    """
    Create all services with SQLite repository.

    Args:
        db_path: Path to SQLite database file

    Returns:
        Tuple of (order_service, debt_service, payment_service)
    """
    repository = SQLiteRepository(db_path)
    order_service = OrderService(repository)
    debt_service = DebtService(repository)
    payment_service = PaymentService(repository)

    return order_service, debt_service, payment_service


async def main():
    """Main entry point."""
    logger.info("Starting bot...")

    # Get token
    token = get_bot_token()

    # Create bot and dispatcher
    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Create services
    db_path = os.getenv('DB_PATH', 'debts.db')
    order_service, debt_service, payment_service = create_services(db_path)

    # Register handlers
    router = create_router(order_service, debt_service, payment_service)
    dp.include_router(router)

    # Start polling
    logger.info("Bot started successfully")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

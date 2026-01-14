"""
Telegram bot handlers using aiogram.

Thin handlers that parse input, call domain services, and format output.
All business logic lives in domain services.
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from decimal import Decimal

from src.domain.services import OrderService, DebtService, PaymentService
from src.domain.exceptions import ValidationError, DebtNotFoundError, PaymentExceedsDebtError
from .parsers import (
    parse_order_command,
    parse_payment_command,
    is_order_command,
    ParseError,
)
from .formatters import (
    format_order_confirmation,
    format_payment_confirmation,
    format_debt_list,
    format_owed_list,
    format_all_debts,
    format_error,
    format_welcome,
    format_help,
)


def create_router(
    order_service: OrderService,
    debt_service: DebtService,
    payment_service: PaymentService,
) -> Router:
    """
    Create aiogram router with all handlers.

    Args:
        order_service: Service for order operations
        debt_service: Service for debt operations
        payment_service: Service for payment operations

    Returns:
        Configured Router instance
    """
    router = Router()

    @router.message(Command("start"))
    async def handle_start(message: Message):
        """Handle /start command."""
        await message.answer(format_welcome())

    @router.message(Command("help", "помощь"))
    async def handle_help(message: Message):
        """Handle /help command."""
        await message.answer(format_help())

    @router.message(Command("debts", "долги"))
    async def handle_debts(message: Message):
        """Handle /debts command - show user's debts."""
        username = message.from_user.username
        if not username:
            await message.answer("❌ У вас не установлен username в Telegram")
            return

        result = debt_service.get_debts_by_user(username)
        await message.answer(format_debt_list(result))

    @router.message(Command("owed", "мнедолжны"))
    async def handle_owed(message: Message):
        """Handle /owed command - show who owes user."""
        username = message.from_user.username
        if not username:
            await message.answer("❌ У вас не установлен username в Telegram")
            return

        result = debt_service.get_debts_to_user(username)
        await message.answer(format_owed_list(result))

    @router.message(Command("all", "все"))
    async def handle_all_debts(message: Message):
        """Handle /all command - show all group debts."""
        result = debt_service.get_all_debts()
        await message.answer(format_all_debts(result))

    @router.message(Command("paid"))
    async def handle_paid(message: Message):
        """Handle /paid command - record payment."""
        username = message.from_user.username
        if not username:
            await message.answer("❌ У вас не установлен username в Telegram")
            return

        try:
            parsed = parse_payment_command(message.text)

            # Get current debt before payment
            current_debt = debt_service.get_debt(username, parsed.creditor)

            # Record payment
            payment_service.record_payment(
                debtor=username,
                creditor=parsed.creditor,
                amount=parsed.amount
            )

            # Calculate remaining debt
            remaining = current_debt - parsed.amount

            await message.answer(
                format_payment_confirmation(parsed.amount, parsed.creditor, remaining)
            )

        except ParseError as e:
            await message.answer(format_error(e))
        except (ValidationError, DebtNotFoundError, PaymentExceedsDebtError) as e:
            await message.answer(format_error(e))

    @router.message(F.text)
    async def handle_text(message: Message):
        """Handle plain text - check if it's an order command."""
        if not message.text:
            return

        # Check if this looks like an order command
        if not is_order_command(message.text):
            return  # Ignore non-order messages

        username = message.from_user.username
        if not username:
            await message.answer("❌ У вас не установлен username в Telegram")
            return

        try:
            parsed = parse_order_command(message.text)

            # Create order (use explicit payer from paid: marker or message sender)
            order = order_service.create_order(
                description=parsed.description or "заказ",
                amount=parsed.amount,
                payer=parsed.payer or username,
                participants=parsed.participants
            )

            # Generate debts
            debt_service.create_debts_from_order(order)

            await message.answer(format_order_confirmation(order))

        except ParseError as e:
            await message.answer(format_error(e))
        except ValidationError as e:
            await message.answer(format_error(e))

    return router

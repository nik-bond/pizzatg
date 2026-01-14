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
    format_consolidated_debts,
    format_error,
    format_welcome,
    format_help,
    format_delete_confirmation,
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

    @router.message(Command("debts", "долги", "balance", "баланс"))
    async def handle_debts(message: Message):
        """Handle /debts command - show consolidated debt balance."""
        username = message.from_user.username
        if not username:
            await message.answer("❌ У вас не установлен username в Telegram")
            return

        chat_id = message.chat.id
        result = debt_service.get_consolidated_debts(username, chat_id)
        await message.answer(format_consolidated_debts(result))

    @router.message(Command("owed", "мнедолжны"))
    async def handle_owed(message: Message):
        """Handle /owed command - show who owes user (without netting)."""
        username = message.from_user.username
        if not username:
            await message.answer("❌ У вас не установлен username в Telegram")
            return

        chat_id = message.chat.id
        result = debt_service.get_debts_to_user(username, chat_id)
        await message.answer(format_owed_list(result))

    @router.message(Command("all", "все"))
    async def handle_all_debts(message: Message):
        """Handle /all command - show all group debts."""
        chat_id = message.chat.id
        result = debt_service.get_all_debts(chat_id)
        await message.answer(format_all_debts(result))

    @router.message(Command("delete", "удалить"))
    async def handle_delete(message: Message):
        """Handle /delete command - delete last order."""
        username = message.from_user.username
        if not username:
            await message.answer("❌ У вас не установлен username в Telegram")
            return

        chat_id = message.chat.id
        # Get last order by this user in this chat
        last_order = order_service.get_last_order(username, chat_id)
        
        if not last_order:
            await message.answer("❌ У вас нет заказов для удаления")
            return

        # Delete associated debts first
        debt_service.delete_debts_for_order(last_order)
        
        # Delete the order
        order_service.delete_order(last_order.id)
        
        await message.answer(format_delete_confirmation(last_order))

    @router.message(Command("paid"))
    async def handle_paid(message: Message):
        """Handle /paid command - record payment."""
        username = message.from_user.username
        if not username:
            await message.answer("❌ У вас не установлен username в Telegram")
            return

        chat_id = message.chat.id
        try:
            parsed = parse_payment_command(message.text)

            # Get current debt before payment
            current_debt = debt_service.get_debt(username, parsed.creditor, chat_id)

            # Record payment
            payment_service.record_payment(
                debtor=username,
                creditor=parsed.creditor,
                amount=parsed.amount,
                chat_id=chat_id
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

        chat_id = message.chat.id
        try:
            parsed = parse_order_command(message.text)

            # Create order (use explicit payer from payer: marker; otherwise payer is the sender)
            payer = parsed.payer or username
            order = order_service.create_order(
                description=parsed.description or "заказ",
                amount=parsed.amount,
                payer=payer,
                participants=parsed.participants,
                created_by=username,
                chat_id=chat_id
            )

            # Generate debts
            debt_service.create_debts_from_order(order)

            await message.answer(format_order_confirmation(order))

        except ParseError as e:
            await message.answer(format_error(e))
        except ValidationError as e:
            await message.answer(format_error(e))

    return router

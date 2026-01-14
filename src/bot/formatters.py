"""
Response formatters for Telegram bot.

Format domain data into user-friendly Telegram messages.
"""
from decimal import Decimal
from typing import Optional

from src.domain.models import Order, Payment


def format_debt_list(debts_result: dict) -> str:
    """
    Format debt list for display.

    Args:
        debts_result: Result from DebtService.get_debts_by_user()

    Returns:
        Formatted message string
    """
    message = debts_result.get('message')
    if message:
        return message

    debts = debts_result.get('debts', [])
    if not debts:
        return "Долгов нет"

    lines = ["📋 Ваши долги:\n"]

    for debt in debts:
        creditor = debt['creditor']
        amount = debt['amount']
        lines.append(f"  → @{creditor}: {amount:.0f} ₽")

    total = debts_result.get('total', Decimal('0'))
    lines.append(f"\n💰 Итого: {total:.0f} ₽")

    return "\n".join(lines)


def format_owed_list(owed_result: dict) -> str:
    """
    Format list of who owes user.

    Args:
        owed_result: Result from DebtService.get_debts_to_user()

    Returns:
        Formatted message string
    """
    message = owed_result.get('message')
    if message:
        return message

    debts = owed_result.get('debts', [])
    if not debts:
        return "Вам никто не должен"

    lines = ["📋 Вам должны:\n"]

    for debt in debts:
        debtor = debt['debtor']
        amount = debt['amount']
        lines.append(f"  ← @{debtor}: {amount:.0f} ₽")

    total = owed_result.get('total', Decimal('0'))
    lines.append(f"\n💰 Итого: {total:.0f} ₽")

    return "\n".join(lines)


def format_order_confirmation(order: Order) -> str:
    """
    Format order creation confirmation.

    Args:
        order: Created order

    Returns:
        Formatted confirmation message
    """
    participants_str = ", ".join(f"@{p}" for p in order.participants)

    return (
        f"✅ Заказ создан!\n\n"
        f"📝 {order.description}\n"
        f"💵 Сумма: {order.amount:.0f} ₽\n"
        f"👥 Участники: {participants_str}\n"
        f"💰 На каждого: {order.per_person_amount:.2f} ₽"
    )


def format_payment_confirmation(
    amount: Decimal,
    creditor: str,
    remaining: Decimal
) -> str:
    """
    Format payment confirmation.

    Args:
        amount: Amount paid
        creditor: Who received payment
        remaining: Remaining debt

    Returns:
        Formatted confirmation message
    """
    if remaining <= 0:
        return (
            f"✅ Оплачено: {amount:.0f} ₽ → @{creditor}\n"
            f"🎉 Долг полностью погашен!"
        )
    else:
        return (
            f"✅ Оплачено: {amount:.0f} ₽ → @{creditor}\n"
            f"📊 Остаток: {remaining:.0f} ₽"
        )


def format_error(error: Exception) -> str:
    """
    Format error message for user.

    Args:
        error: Exception that occurred

    Returns:
        User-friendly error message
    """
    return f"❌ Ошибка: {str(error)}"


def format_welcome() -> str:
    """Format welcome message for /start command."""
    return (
        "👋 Привет! Я бот для учёта совместных расходов.\n\n"
        "📖 Как пользоваться:\n\n"
        "1️⃣ Создать заказ:\n"
        "   пицца 3000 @ivan @petya @masha\n\n"
        "2️⃣ Отметить оплату:\n"
        "   /paid @ivan 1000\n\n"
        "3️⃣ Посмотреть долги:\n"
        "   /debts - ваши долги\n"
        "   /owed - кто вам должен\n\n"
        "❓ /help - справка по командам"
    )


def format_help() -> str:
    """Format help message with command list."""
    return (
        "📖 Команды бота:\n\n"
        "📝 Создание заказа:\n"
        "   описание сумма @участник1 @участник2 ...\n"
        "   Пример: пицца 3000 @ivan @petya\n\n"
        "💸 Оплата долга:\n"
        "   /paid @кому сумма\n"
        "   Пример: /paid @ivan 1000\n\n"
        "📋 Просмотр долгов:\n"
        "   /debts - мои долги\n"
        "   /owed - кто мне должен\n\n"
        "ℹ️ Другое:\n"
        "   /start - начало работы\n"
        "   /help - эта справка"
    )


def format_all_debts(debts_result: dict) -> str:
    """
    Format all group debts.

    Args:
        debts_result: Result from DebtService.get_all_debts()

    Returns:
        Formatted message string
    """
    debts = debts_result.get('debts', [])

    if not debts:
        return "🎉 В группе нет долгов!"

    lines = ["📊 Все долги в группе:\n"]

    for debt in debts:
        debtor = debt['debtor']
        creditor = debt['creditor']
        amount = debt['amount']
        lines.append(f"  @{debtor} → @{creditor}: {amount:.0f} ₽")

    total = debts_result.get('total', Decimal('0'))
    lines.append(f"\n💰 Общая сумма: {total:.0f} ₽")

    return "\n".join(lines)

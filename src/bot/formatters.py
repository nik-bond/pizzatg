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
        description = debt.get('description', '')
        if description:
            lines.append(f"  → @{creditor}: {amount:.0f} ₽ ({description})")
        else:
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
        description = debt.get('description', '')
        if description:
            lines.append(f"  ← @{debtor}: {amount:.0f} ₽ ({description})")
        else:
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
        f"💳 Оплатил: @{order.payer}\n"
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


def format_delete_confirmation(order: Order) -> str:
    """
    Format order deletion confirmation.

    Args:
        order: Deleted order

    Returns:
        Formatted confirmation message
    """
    participants_str = ", ".join(f"@{p}" for p in order.participants)
    
    return (
        f"🗑️ Заказ удалён!\n\n"
        f"📝 {order.description}\n"
        f"💵 Сумма: {order.amount:.0f} ₽\n"
        f"💳 Платил: @{order.payer}\n"
        f"👥 Участники: {participants_str}\n\n"
        f"Связанные долги также удалены."
    )


def format_welcome() -> str:
    """Format welcome message for /start command."""
    return (
        "👋 Привет! Я бот для учёта совместных расходов.\n\n"
        "📖 Как пользоваться:\n\n"
        "1️⃣ Создать заказ (первый платит):\n"
        "   пицца 3000 @ivan @petya @masha\n"
        "   💡 @ivan платит, остальные должны ему\n\n"
        "1️⃣ Создать заказ (указать плательщика):\n"
        "   пицца 3000 payer:@ivan @petya @masha\n\n"
        "2️⃣ Отметить оплату:\n"
        "   /paid @ivan 1000\n\n"
        "3️⃣ Посмотреть долги:\n"
        "   /debts - ваши долги\n"
        "   /owed - кто вам должен\n\n"
        "🗑️ /delete - удалить последний заказ\n\n"
        "❓ /help - справка по командам"
    )


def format_help() -> str:
    """Format help message with command list."""
    return (
        "📖 Команды бота:\n\n"
        "1️⃣ Создать заказ (первый платит):\n"
        "   описание сумма @плательщик @участник2 ...\n\n"
        "   Пример: пицца 3000 @ivan @petya\n"
        "   💡 @ivan - плательщик, @petya ему должен\n\n"
        "1️⃣ Создать заказ (указать плательщика):\n"
        "   описание сумма payer:@плательщик @участник1 ...\n\n"
        "   Пример: пицца 3000 payer:@ivan @petya @masha\n"
        "   💡 @ivan заплатил, остальные ему должны\n\n\n"
        "2️⃣ Отметить оплату:\n"
        "   /paid @кому сумма\n\n"
        "   Пример: /paid @ivan 1000\n\n\n"
        "3️⃣ Посмотреть долги:\n"
        "   /debts - ваши долги (с взаимозачётом)\n"
        "   /owed - кто вам должен (с взаимозачётом)\n\n"
        "   💡 Взаимозачёт: если вы должны 400₽ за десерт,\n"
        "      но вам должны 200₽ за кофе → итого: 200₽\n\n\n"
        "🗑️ Удалить заказ:\n"
        "   /delete - удалить последний созданный заказ\n\n\n"
        "❓ Справка:\n"
        "   /help - эта справка"
    )


def format_consolidated_debts(result: dict) -> str:
    """
    Format consolidated debt view with netting and breakdown.

    Shows net balance with each person, including what makes up the balance.

    Args:
        result: Result from DebtService.get_consolidated_debts()

    Returns:
        Formatted message string
    """
    message = result.get('message')
    if message:
        return message

    debts = result.get('debts', [])
    if not debts:
        return "🎉 Нет долгов!"

    lines = ["📊 Баланс долгов:\n"]

    for debt in debts:
        cp = debt['counterparty']
        i_owe = debt['i_owe']
        they_owe = debt['they_owe']
        net_amount = debt['net_amount']
        direction = debt['net_direction']

        lines.append(f"👤 @{cp}:")

        # Show breakdown
        if i_owe:
            desc = f" ({i_owe['description']})" if i_owe['description'] else ""
            lines.append(f"   ↑ Я должен: {i_owe['amount']:.0f} ₽{desc}")

        if they_owe:
            desc = f" ({they_owe['description']})" if they_owe['description'] else ""
            lines.append(f"   ↓ Мне должен: {they_owe['amount']:.0f} ₽{desc}")

        # Show net result
        if direction == 'i_owe':
            lines.append(f"   ═══ Итого: я должен {net_amount:.0f} ₽")
        elif direction == 'they_owe':
            lines.append(f"   ═══ Итого: мне должен {net_amount:.0f} ₽")
        else:
            lines.append(f"   ═══ Итого: квиты!")

        lines.append("")  # Empty line between people

    # Summary
    total_i_owe = result.get('total_i_owe', Decimal('0'))
    total_they_owe = result.get('total_they_owe', Decimal('0'))

    if total_i_owe > 0 and total_they_owe > 0:
        lines.append(f"💰 Общий баланс:")
        lines.append(f"   Я должен: {total_i_owe:.0f} ₽")
        lines.append(f"   Мне должны: {total_they_owe:.0f} ₽")
    elif total_i_owe > 0:
        lines.append(f"💰 Всего я должен: {total_i_owe:.0f} ₽")
    elif total_they_owe > 0:
        lines.append(f"💰 Всего мне должны: {total_they_owe:.0f} ₽")

    return "\n".join(lines)


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
        description = debt.get('description', '')
        if description:
            lines.append(f"  @{debtor} → @{creditor}: {amount:.0f} ₽ ({description})")
        else:
            lines.append(f"  @{debtor} → @{creditor}: {amount:.0f} ₽")

    total = debts_result.get('total', Decimal('0'))
    lines.append(f"\n💰 Общая сумма: {total:.0f} ₽")

    return "\n".join(lines)

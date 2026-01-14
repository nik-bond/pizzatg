"""
Message parsers for Telegram bot.

Parse incoming messages into structured data for domain services.
Handles various input formats and normalizes usernames.
"""
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional


@dataclass
class ParsedOrder:
    """Parsed order command data."""
    description: str
    amount: Decimal
    participants: list[str]


@dataclass
class ParsedPayment:
    """Parsed payment command data."""
    creditor: str
    amount: Decimal


class ParseError(Exception):
    """Raised when message parsing fails."""
    pass


def normalize_username(username: str) -> str:
    """
    Normalize username by removing @ prefix.

    Args:
        username: Raw username (may include @)

    Returns:
        Normalized username without @
    """
    return username.lstrip('@').strip()


def parse_order_command(text: str) -> ParsedOrder:
    """
    Parse order command from message text.

    Formats supported:
    - "пицца 3000 @ivan @petya @masha" (with description)
    - "3000 @ivan @petya" (without description)

    Args:
        text: Raw message text

    Returns:
        ParsedOrder with description, amount, participants

    Raises:
        ParseError: If message format is invalid
    """
    # Find all @mentions
    mentions = re.findall(r'@(\w+)', text)

    if not mentions:
        raise ParseError("Не найдены участники. Укажите пользователей через @")

    # Remove mentions from text to find description and amount
    text_without_mentions = re.sub(r'@\w+', '', text).strip()

    # Try to find amount (integer)
    amount_match = re.search(r'\b(\d+)\b', text_without_mentions)

    if not amount_match:
        raise ParseError("Не найдена сумма. Укажите сумму числом")

    try:
        amount = Decimal(amount_match.group(1))
    except InvalidOperation:
        raise ParseError("Некорректная сумма")

    # Description is everything before the amount (excluding the amount itself)
    amount_pos = text_without_mentions.find(amount_match.group(1))
    description = text_without_mentions[:amount_pos].strip()

    # Normalize participants
    participants = [normalize_username(m) for m in mentions]

    return ParsedOrder(
        description=description,
        amount=amount,
        participants=participants
    )


def parse_payment_command(text: str) -> ParsedPayment:
    """
    Parse payment command from message text.

    Formats supported:
    - "/paid @ivan 1000"
    - "/paid ivan 500"

    Args:
        text: Raw message text

    Returns:
        ParsedPayment with creditor and amount

    Raises:
        ParseError: If message format is invalid
    """
    # Remove /paid prefix
    text = re.sub(r'^/paid\s*', '', text, flags=re.IGNORECASE).strip()

    if not text:
        raise ParseError("Формат: /paid @username сумма")

    # Try to find @mention first
    mention_match = re.search(r'@?(\w+)', text)
    if not mention_match:
        raise ParseError("Укажите кому платите")

    creditor = normalize_username(mention_match.group(1))

    # Find amount after username
    remaining = text[mention_match.end():].strip()
    amount_match = re.search(r'\b(\d+)\b', remaining)

    if not amount_match:
        # Try to find amount anywhere in text
        amount_match = re.search(r'\b(\d+)\b', text)
        if not amount_match:
            raise ParseError("Укажите сумму платежа")

    try:
        amount = Decimal(amount_match.group(1))
    except InvalidOperation:
        raise ParseError("Некорректная сумма")

    return ParsedPayment(
        creditor=creditor,
        amount=amount
    )


def is_order_command(text: str) -> bool:
    """
    Check if message looks like an order command.

    Order commands contain @ mentions and a number.
    """
    has_mention = bool(re.search(r'@\w+', text))
    has_number = bool(re.search(r'\b\d+\b', text))
    is_other_command = text.startswith('/')

    return has_mention and has_number and not is_other_command


def is_payment_command(text: str) -> bool:
    """Check if message is a payment command."""
    return text.lower().startswith('/paid')


def is_debts_command(text: str) -> bool:
    """Check if message is a debts query command."""
    return text.lower().startswith('/debts') or text.lower().startswith('/долги')


def is_owed_command(text: str) -> bool:
    """Check if message is an owed query command."""
    return text.lower().startswith('/owed') or text.lower().startswith('/мнедолжны')


def is_start_command(text: str) -> bool:
    """Check if message is /start command."""
    return text.lower().startswith('/start')


def is_help_command(text: str) -> bool:
    """Check if message is /help command."""
    return text.lower().startswith('/help') or text.lower().startswith('/помощь')

"""BDD step definitions for end-to-end bot handler workflows.

These scenarios test full flows:
message -> handler -> service -> response.

We simulate Telegram interactions by creating aiogram Message mocks and
calling the router handler callbacks directly.
"""

from __future__ import annotations

from decimal import Decimal
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import Chat, Message, User
from pytest_bdd import scenarios, given, when, then, parsers


scenarios("../features/bot_integration.feature")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def bot_flow_context(context):
    """Reuse shared context but add bot-specific fields."""
    # context is a dict-like object (see tests/conftest.py)
    context.router = None
    context.chat_id = 0
    context.last_message = None
    context.last_response = None
    return context


def _create_message(*, text: str, username: str | None, chat_id: int) -> Message:
    message = MagicMock(spec=Message)
    message.text = text
    message.from_user = User(
        id=12345,
        is_bot=False,
        first_name="Test",
        username=username,
    )
    message.chat = Chat(id=chat_id, type="private")

    # Track responses written by handlers.
    message.responses = []

    async def answer_mock(text, **kwargs):
        message.responses.append(text)
        return MagicMock()

    message.answer = AsyncMock(side_effect=answer_mock)

    return message


async def _call_handler(router, handler_name: str, message: Message) -> None:
    observers = router.observers["message"]
    for observer in observers.handlers:
        handler_func = observer.callback
        if getattr(handler_func, "__name__", None) == handler_name:
            await handler_func(message)
            return

    raise ValueError(f"Handler {handler_name} not found")


def _handler_for_text(text: str) -> str:
    if text.startswith("/start"):
        return "handle_start"
    if text.startswith("/help"):
        return "handle_help"
    if text.startswith("/debts"):
        return "handle_debts"
    if text.startswith("/owed"):
        return "handle_owed"
    if text.startswith("/paid"):
        return "handle_paid"
    return "handle_text"


# ---------------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------------

@given("a router with in-memory services")
def given_router(bot_flow_context, router):
    bot_flow_context.router = router


@given(parsers.parse("chat id {chat_id:d}"))
def given_chat_id(bot_flow_context, chat_id: int):
    bot_flow_context.chat_id = chat_id


@given(parsers.parse('an order "{description}" for {amount:d} rubles paid by "{payer}" with participants "{participants}"'))
def given_order(order_service, debt_service, bot_flow_context, description: str, amount: int, payer: str, participants: str):
    participant_list = [p.strip() for p in participants.split(",") if p.strip()]
    order = order_service.create_order(
        description=description,
        amount=Decimal(amount),
        payer=payer,
        participants=participant_list,
        created_by=payer,
        chat_id=bot_flow_context.chat_id,
    )
    debt_service.create_debts_from_order(order)


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------

@when(parsers.parse('user "{username}" sends message "{text}"'))
def when_user_sends_message(bot_flow_context, username: str, text: str):
    message = _create_message(text=text, username=username, chat_id=bot_flow_context.chat_id)
    bot_flow_context.last_message = message

    handler_name = _handler_for_text(text)
    asyncio.run(_call_handler(bot_flow_context.router, handler_name, message))

    bot_flow_context.last_response = message.responses[-1] if message.responses else None


@when(parsers.parse('user without username sends message "{text}"'))
def when_user_without_username_sends_message(bot_flow_context, text: str):
    message = _create_message(text=text, username=None, chat_id=bot_flow_context.chat_id)
    bot_flow_context.last_message = message

    handler_name = _handler_for_text(text)
    asyncio.run(_call_handler(bot_flow_context.router, handler_name, message))

    bot_flow_context.last_response = message.responses[-1] if message.responses else None


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------

@then(parsers.parse("exactly {count:d} response is sent"))
def then_exactly_one_response(bot_flow_context, count: int):
    assert bot_flow_context.last_message is not None
    assert len(bot_flow_context.last_message.responses) == count


@then(parsers.parse('response contains "{text}"'))
def then_response_contains(bot_flow_context, text: str):
    assert bot_flow_context.last_response is not None, "No response captured"
    assert text in bot_flow_context.last_response


@then(parsers.parse('response contains one of "{options}"'))
def then_response_contains_one_of(bot_flow_context, options: str):
    assert bot_flow_context.last_response is not None, "No response captured"
    parts = [p for p in options.split("|") if p]
    assert any(p in bot_flow_context.last_response for p in parts), (
        f"Expected response to contain one of {parts}, got: {bot_flow_context.last_response!r}"
    )


@then(parsers.parse('debt from "{debtor}" to "{creditor}" is {amount:d} rubles'))
def then_debt_amount(debt_service, bot_flow_context, debtor: str, creditor: str, amount: int):
    actual = debt_service.get_debt(debtor, creditor, bot_flow_context.chat_id)
    assert actual == Decimal(amount), f"Expected {debtor}->{creditor} debt {amount}, got {actual}"

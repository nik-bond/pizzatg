"""
Step definitions for Telegram bot command tests.

Tests parsers and formatters without actual Telegram API.
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from decimal import Decimal

from src.bot.parsers import parse_order_command, parse_payment_command, ParseError
from src.bot.formatters import (
    format_debt_list,
    format_owed_list,
    format_order_confirmation,
    format_payment_confirmation,
    format_error,
    format_welcome,
    format_help,
)
from src.domain.models import Order

# Load scenarios
scenarios('../features/bot_commands.feature')


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def bot_context():
    """Context for bot tests."""
    class Context:
        def __init__(self):
            self.message_text = None
            self.parsed_order = None
            self.parsed_payment = None
            self.debts = []
            self.order = None
            self.payment_amount = None
            self.creditor = None
            self.remaining_debt = None
            self.error = None
            self.response = None

    return Context()


# ---------------------------------------------------------------------------
# GIVEN steps
# ---------------------------------------------------------------------------

@given(parsers.parse('message text "{text}"'))
def set_message_text(bot_context, text: str):
    """Set message text for parsing."""
    bot_context.message_text = text


@given(parsers.parse('user has debt of {amount:d} to "{creditor}"'))
def add_user_debt(bot_context, amount: int, creditor: str):
    """Add a debt for user."""
    if not hasattr(bot_context, 'debts') or bot_context.debts is None:
        bot_context.debts = []
    bot_context.debts.append({
        'creditor': creditor,
        'amount': Decimal(amount)
    })


@given('user has no debts')
def set_no_debts(bot_context):
    """Set up empty debts."""
    bot_context.debts = []


@given(parsers.parse('order "{description}" for {amount:d} rubles with {count:d} participants'))
def set_order_for_formatting(bot_context, description: str, amount: int, count: int):
    """Create order for formatting."""
    participants = [f"user{i}" for i in range(1, count + 1)]
    per_person = Decimal(amount) / count

    bot_context.order = Order(
        id="test123",
        description=description,
        amount=Decimal(amount),
        payer="user1",
        participants=participants,
        per_person_amount=per_person.quantize(Decimal('0.01'))
    )


@given(parsers.parse('payment of {amount:d} rubles to "{creditor}"'))
def set_payment_for_formatting(bot_context, amount: int, creditor: str):
    """Set payment details for formatting."""
    bot_context.payment_amount = Decimal(amount)
    bot_context.creditor = creditor


@given(parsers.parse('remaining debt is {amount:d} rubles'))
def set_remaining_debt(bot_context, amount: int):
    """Set remaining debt after payment."""
    bot_context.remaining_debt = Decimal(amount)


@given(parsers.parse('validation error "{message}"'))
def set_validation_error(bot_context, message: str):
    """Set validation error for formatting."""
    from src.domain.exceptions import ValidationError
    bot_context.error = ValidationError(message)


@given(parsers.parse('user "{username}" has debt of {amount:d} to "{creditor}"'))
def set_single_debt(bot_context, username: str, amount: int, creditor: str):
    """Set up single debt for user."""
    bot_context.debts = [{
        'creditor': creditor,
        'amount': Decimal(amount)
    }]
    bot_context.username = username


@given(parsers.parse('"{debtor}" owes "{creditor}" {amount:d} rubles'))
def set_debt_for_owed(bot_context, debtor: str, creditor: str, amount: int):
    """Set up debt for owed list."""
    if not hasattr(bot_context, 'owed_debts'):
        bot_context.owed_debts = []
    bot_context.owed_debts.append({
        'debtor': debtor,
        'amount': Decimal(amount)
    })


# ---------------------------------------------------------------------------
# WHEN steps
# ---------------------------------------------------------------------------

@when('the message is parsed as order command')
def parse_as_order(bot_context):
    """Parse message as order command."""
    try:
        bot_context.parsed_order = parse_order_command(bot_context.message_text)
    except ParseError as e:
        bot_context.error = e


@when('the message is parsed as payment command')
def parse_as_payment(bot_context):
    """Parse message as payment command."""
    try:
        bot_context.parsed_payment = parse_payment_command(bot_context.message_text)
    except ParseError as e:
        bot_context.error = e


@when('debt list is formatted')
def format_debts(bot_context):
    """Format debt list."""
    if bot_context.debts:
        total = sum(d['amount'] for d in bot_context.debts)
        result = {'debts': bot_context.debts, 'total': total, 'message': None}
    else:
        result = {'debts': [], 'total': Decimal('0'), 'message': 'Долгов нет'}

    bot_context.response = format_debt_list(result)


@when('order confirmation is formatted')
def format_order(bot_context):
    """Format order confirmation."""
    bot_context.response = format_order_confirmation(bot_context.order)


@when('payment confirmation is formatted')
def format_payment(bot_context):
    """Format payment confirmation."""
    bot_context.response = format_payment_confirmation(
        bot_context.payment_amount,
        bot_context.creditor,
        bot_context.remaining_debt
    )


@when('error is formatted')
def format_err(bot_context):
    """Format error message."""
    bot_context.response = format_error(bot_context.error)


@when(parsers.parse('user sends "{command}" command'))
def user_sends_command(bot_context, command: str):
    """Simulate user sending command."""
    if command == '/start':
        bot_context.response = format_welcome()
    elif command == '/help':
        bot_context.response = format_help()


@when(parsers.parse('"{username}" sends "{command}" command'))
def specific_user_sends_command(bot_context, username: str, command: str):
    """Simulate specific user sending command."""
    if command == '/debts':
        if bot_context.debts:
            total = sum(d['amount'] for d in bot_context.debts)
            result = {'debts': bot_context.debts, 'total': total, 'message': None}
        else:
            result = {'debts': [], 'total': Decimal('0'), 'message': 'Долгов нет'}
        bot_context.response = format_debt_list(result)
    elif command == '/owed':
        if hasattr(bot_context, 'owed_debts') and bot_context.owed_debts:
            total = sum(d['amount'] for d in bot_context.owed_debts)
            result = {'debts': bot_context.owed_debts, 'total': total, 'message': None}
        else:
            result = {'debts': [], 'total': Decimal('0'), 'message': 'Вам никто не должен'}
        bot_context.response = format_owed_list(result)


# ---------------------------------------------------------------------------
# THEN steps
# ---------------------------------------------------------------------------

@then(parsers.parse('parsed description is "{expected}"'))
def verify_parsed_description(bot_context, expected: str):
    """Verify parsed description."""
    assert bot_context.parsed_order.description == expected, \
        f"Expected description '{expected}', got '{bot_context.parsed_order.description}'"


@then('parsed description is empty')
def verify_parsed_description_empty(bot_context):
    """Verify parsed description is empty."""
    assert bot_context.parsed_order.description == "", \
        f"Expected empty description, got '{bot_context.parsed_order.description}'"


@then(parsers.parse('parsed amount is {expected:d}'))
def verify_parsed_amount(bot_context, expected: int):
    """Verify parsed amount."""
    assert bot_context.parsed_order.amount == Decimal(expected), \
        f"Expected amount {expected}, got {bot_context.parsed_order.amount}"


@then(parsers.parse('parsed participants are "{expected}"'))
def verify_parsed_participants(bot_context, expected: str):
    """Verify parsed participants."""
    expected_list = [p.strip().strip('"') for p in expected.split(',')]
    assert bot_context.parsed_order.participants == expected_list, \
        f"Expected participants {expected_list}, got {bot_context.parsed_order.participants}"


@then(parsers.parse('parsed payer is "{expected}"'))
def verify_parsed_payer(bot_context, expected: str):
    """Verify parsed explicit payer."""
    assert bot_context.parsed_order.payer == expected, \
        f"Expected payer '{expected}', got '{bot_context.parsed_order.payer}'"


@then('parsed payer is not specified')
def verify_parsed_payer_not_specified(bot_context):
    """Verify no explicit payer was specified."""
    assert bot_context.parsed_order.payer is None, \
        f"Expected no payer, got '{bot_context.parsed_order.payer}'"


@then(parsers.parse('parsed creditor is "{expected}"'))
def verify_parsed_creditor(bot_context, expected: str):
    """Verify parsed creditor."""
    assert bot_context.parsed_payment.creditor == expected, \
        f"Expected creditor '{expected}', got '{bot_context.parsed_payment.creditor}'"


@then(parsers.parse('parsed payment amount is {expected:d}'))
def verify_parsed_payment_amount(bot_context, expected: int):
    """Verify parsed payment amount."""
    assert bot_context.parsed_payment.amount == Decimal(expected), \
        f"Expected amount {expected}, got {bot_context.parsed_payment.amount}"


@then(parsers.parse('response contains "{expected}"'))
def verify_response_contains(bot_context, expected: str):
    """Verify response contains expected text."""
    assert expected in bot_context.response, \
        f"Expected '{expected}' in response:\n{bot_context.response}"


@then(parsers.parse('response contains "{expected}" as per person amount'))
def verify_response_contains_per_person(bot_context, expected: str):
    """Verify response contains expected per-person amount."""
    assert expected in bot_context.response, \
        f"Expected '{expected}' (per person) in response:\n{bot_context.response}"


@then(parsers.parse('response is "{expected}"'))
def verify_response_exact(bot_context, expected: str):
    """Verify exact response."""
    assert bot_context.response == expected, \
        f"Expected '{expected}', got '{bot_context.response}'"


@then('bot responds with welcome message')
def verify_welcome_response(bot_context):
    """Verify welcome response."""
    assert 'Привет' in bot_context.response or 'пользоваться' in bot_context.response


@then('response contains usage instructions')
def verify_usage_instructions(bot_context):
    """Verify response contains usage instructions."""
    assert 'пицца' in bot_context.response.lower() or '@' in bot_context.response


@then('bot responds with command list')
def verify_command_list(bot_context):
    """Verify command list response."""
    assert '/debts' in bot_context.response or '/paid' in bot_context.response


@then('bot responds with debt list')
def verify_debt_list_response(bot_context):
    """Verify debt list response."""
    assert '₽' in bot_context.response or 'долг' in bot_context.response.lower()


@then('bot responds with creditor list')
def verify_creditor_list_response(bot_context):
    """Verify creditor list response."""
    assert '₽' in bot_context.response or 'должн' in bot_context.response.lower()

"""
Step definitions for debt calculation scenarios.

Tests verify that debts are correctly created when orders are made.
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from decimal import Decimal

# Load scenarios
scenarios('../features/debt_calculation.feature')


# ---------------------------------------------------------------------------
# GIVEN steps
# ---------------------------------------------------------------------------

@given(parsers.parse('создан заказ "{description}" на {amount:d} рублей с участниками "{participants}"'))
def create_order_with_participants(context, order_service, debt_service, description: str, amount: int, participants: str):
    """Create an order and generate debts."""
    participant_list = [p.strip().strip('"') for p in participants.split(',')]
    payer = context.payer

    # Create order
    context.order = order_service.create_order(
        description=description,
        amount=Decimal(amount),
        payer=payer,
        participants=participant_list
    )

    # Generate debts from order
    context.debts = debt_service.create_debts_from_order(context.order)


@given(parsers.parse('создан заказ "{description}" на {amount:d} рублей с плательщиком "{payer}" и участниками "{participants}"'))
def create_order_with_explicit_payer(context, order_service, debt_service, description: str, amount: int, payer: str, participants: str):
    """Create an order with explicitly specified payer."""
    participant_list = [p.strip().strip('"') for p in participants.split(',')]

    context.order = order_service.create_order(
        description=description,
        amount=Decimal(amount),
        payer=payer,
        participants=participant_list
    )

    context.debts = debt_service.create_debts_from_order(context.order)


# ---------------------------------------------------------------------------
# WHEN steps
# ---------------------------------------------------------------------------

@when(parsers.parse('запрашивается чистый баланс между "{user1}" и "{user2}"'))
def query_net_balance(context, debt_service, user1: str, user2: str):
    """Query the net balance between two users."""
    context.query_result = debt_service.get_net_balance(user1, user2)


# ---------------------------------------------------------------------------
# THEN steps
# ---------------------------------------------------------------------------

@then(parsers.parse('"{debtor}" должен "{creditor}" {amount:d} рублей'))
def verify_debt_amount(context, debt_service, debtor: str, creditor: str, amount: int):
    """Verify that debtor owes creditor the specified amount."""
    actual_debt = debt_service.get_debt(debtor, creditor)
    expected = Decimal(amount)

    assert actual_debt == expected, \
        f"Expected {debtor} to owe {creditor} {expected}, got {actual_debt}"


@then(parsers.parse('"{user}" никому не должен'))
def verify_no_debts(context, debt_service, user: str):
    """Verify user has no outgoing debts."""
    total_owed = debt_service.get_total_owed_by(user)
    assert total_owed == Decimal('0'), \
        f"Expected {user} to owe nothing, but owes {total_owed}"


@then(parsers.parse('"{user}" не имеет долга перед "{creditor}"'))
def verify_no_debt_to_creditor(context, debt_service, user: str, creditor: str):
    """Verify user has no debt to specific creditor."""
    debt = debt_service.get_debt(user, creditor)
    assert debt == Decimal('0'), \
        f"Expected no debt from {user} to {creditor}, got {debt}"


@then(parsers.parse('чистый баланс равен {amount:d} рублей'))
def verify_net_balance_zero(context, amount: int):
    """Verify net balance equals specified amount."""
    expected = Decimal(amount)
    assert context.query_result['net_balance'] == expected, \
        f"Expected net balance {expected}, got {context.query_result['net_balance']}"


@then(parsers.parse('"{debtor}" должен "{creditor}" чистыми {amount:d} рублей'))
def verify_net_debt(context, debtor: str, creditor: str, amount: int):
    """Verify net debt between two users."""
    expected = Decimal(amount)
    result = context.query_result

    assert result['net_debtor'] == debtor, \
        f"Expected net debtor to be {debtor}, got {result['net_debtor']}"
    assert result['net_creditor'] == creditor, \
        f"Expected net creditor to be {creditor}, got {result['net_creditor']}"
    assert result['net_balance'] == expected, \
        f"Expected net balance {expected}, got {result['net_balance']}"

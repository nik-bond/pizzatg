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

@given(parsers.parse('user "{username}" is the payer'))
def set_payer(context, username: str):
    """Set the payer for the order."""
    context.payer = username


@given(parsers.parse('order "{description}" for {amount:d} rubles is created with participants "{participants}"'))
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


@given(parsers.parse('order "{description}" for {amount:d} rubles is created with payer "{payer}" and participants "{participants}"'))
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

@when(parsers.parse('net balance is requested between "{user1}" and "{user2}"'))
def query_net_balance(context, debt_service, user1: str, user2: str):
    """Query the net balance between two users."""
    context.query_result = debt_service.get_net_balance(user1, user2)


# ---------------------------------------------------------------------------
# THEN steps
# ---------------------------------------------------------------------------

@then(parsers.parse('"{debtor}" owes "{creditor}" {amount:d} rubles'))
def verify_debt_amount(context, debt_service, debtor: str, creditor: str, amount: int):
    """Verify that debtor owes creditor the specified amount."""
    actual_debt = debt_service.get_debt(debtor, creditor)
    expected = Decimal(amount)

    assert actual_debt == expected, \
        f"Expected {debtor} to owe {creditor} {expected}, got {actual_debt}"


@then(parsers.parse('"{user}" owes nothing'))
def verify_no_debts(context, debt_service, user: str):
    """Verify user has no outgoing debts."""
    total_owed = debt_service.get_total_owed_by(user)
    assert total_owed == Decimal('0'), \
        f"Expected {user} to owe nothing, but owes {total_owed}"


@then(parsers.parse('"{user}" has no debt to "{creditor}"'))
def verify_no_debt_to_creditor(context, debt_service, user: str, creditor: str):
    """Verify user has no debt to specific creditor."""
    debt = debt_service.get_debt(user, creditor)
    assert debt == Decimal('0'), \
        f"Expected no debt from {user} to {creditor}, got {debt}"


@then(parsers.parse('net balance is {amount:d} rubles'))
def verify_net_balance_zero(context, amount: int):
    """Verify net balance equals specified amount."""
    expected = Decimal(amount)
    assert context.query_result['net_balance'] == expected, \
        f"Expected net balance {expected}, got {context.query_result['net_balance']}"


@then(parsers.parse('"{debtor}" owes "{creditor}" net {amount:d} rubles'))
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


@when(parsers.parse('consolidated debts are requested for "{user}"'))
def query_consolidated_debts(context, debt_service, user: str):
    """Query consolidated debts for a user."""
    context.consolidated_result = debt_service.get_consolidated_debts(user)


@then(parsers.parse('consolidated result shows "{counterparty}" with net "{direction}" of {amount:d} rubles'))
def verify_consolidated_net(context, counterparty: str, direction: str, amount: int):
    """Verify consolidated debt result."""
    debts = context.consolidated_result['debts']
    found = None
    for d in debts:
        if d['counterparty'] == counterparty:
            found = d
            break

    assert found is not None, f"Counterparty {counterparty} not found in consolidated debts"
    assert found['net_direction'] == direction, \
        f"Expected direction {direction}, got {found['net_direction']}"
    assert found['net_amount'] == Decimal(amount), \
        f"Expected net amount {amount}, got {found['net_amount']}"


@then(parsers.parse('breakdown shows I owe {amount:d} for "{description}"'))
def verify_i_owe_breakdown(context, amount: int, description: str):
    """Verify I owe breakdown in consolidated result."""
    debts = context.consolidated_result['debts']
    # Find the debt with the i_owe entry matching the amount
    found = False
    for d in debts:
        if d['i_owe'] and d['i_owe']['amount'] == Decimal(amount):
            assert description in d['i_owe']['description'], \
                f"Expected description containing '{description}', got '{d['i_owe']['description']}'"
            found = True
            break
    assert found, f"No i_owe entry found with amount {amount}"


@then(parsers.parse('breakdown shows they owe {amount:d} for "{description}"'))
def verify_they_owe_breakdown(context, amount: int, description: str):
    """Verify they owe breakdown in consolidated result."""
    debts = context.consolidated_result['debts']
    # Find the debt with the they_owe entry matching the amount
    found = False
    for d in debts:
        if d['they_owe'] and d['they_owe']['amount'] == Decimal(amount):
            assert description in d['they_owe']['description'], \
                f"Expected description containing '{description}', got '{d['they_owe']['description']}'"
            found = True
            break
    assert found, f"No they_owe entry found with amount {amount}"

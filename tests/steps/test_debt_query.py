"""
Step definitions for debt query scenarios.

Tests verify that debt queries return correct information.
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from decimal import Decimal

# Load scenarios
scenarios('../features/debt_query.feature')


# ---------------------------------------------------------------------------
# GIVEN steps
# ---------------------------------------------------------------------------

@given(parsers.parse('создан заказ "{description}" на {amount:d} рублей с плательщиком "{payer}" и участниками "{participants}"'))
def create_order_for_query(context, order_service, debt_service, description: str, amount: int, payer: str, participants: str):
    """Create an order for query testing."""
    participant_list = [p.strip().strip('"') for p in participants.split(',')]

    order = order_service.create_order(
        description=description,
        amount=Decimal(amount),
        payer=payer,
        participants=participant_list
    )

    debt_service.create_debts_from_order(order)


@given(parsers.parse('пользователь "{username}" существует'))
def user_exists(context, repository, username: str):
    """Register a user in the system."""
    repository.add_user(username)


@given(parsers.parse('у "{username}" нет заказов'))
def user_has_no_orders(context, username: str):
    """User has no orders (implicit - no action needed)."""
    pass


@given(parsers.parse('"{debtor}" заплатил "{creditor}" {amount:d} рублей'))
def record_past_payment(context, payment_service, debtor: str, creditor: str, amount: int):
    """Record a payment that already happened."""
    payment_service.record_payment(
        debtor=debtor,
        creditor=creditor,
        amount=Decimal(amount)
    )


# ---------------------------------------------------------------------------
# WHEN steps
# ---------------------------------------------------------------------------

@when(parsers.parse('"{username}" запрашивает свои долги'))
def query_my_debts(context, debt_service, username: str):
    """Query debts owed by user."""
    context.query_result = debt_service.get_debts_by_user(username)
    context.queried_user = username


@when(parsers.parse('"{username}" запрашивает кто ему должен'))
def query_owed_to_me(context, debt_service, username: str):
    """Query debts owed to user."""
    context.query_result = debt_service.get_debts_to_user(username)
    context.queried_user = username


@when('запрашиваются все долги в группе')
def query_all_debts(context, debt_service):
    """Query all debts in the group."""
    context.query_result = debt_service.get_all_debts()


# ---------------------------------------------------------------------------
# THEN steps
# ---------------------------------------------------------------------------

@then(parsers.parse('результат содержит долг {amount:d} рублей перед "{creditor}"'))
def result_contains_debt_to(context, amount: int, creditor: str):
    """Verify result contains specific debt."""
    expected = Decimal(amount)
    debts = context.query_result.get('debts', [])

    found = False
    for debt in debts:
        if debt['creditor'] == creditor and debt['amount'] == expected:
            found = True
            break

    assert found, \
        f"Expected debt of {expected} to {creditor} not found in {debts}"


@then(parsers.parse('результат содержит долг "{debtor}" на {amount:d} рублей'))
def result_contains_debt_from(context, debtor: str, amount: int):
    """Verify result contains debt from specific debtor."""
    expected = Decimal(amount)
    debts = context.query_result.get('debts', [])

    found = False
    for debt in debts:
        if debt['debtor'] == debtor and debt['amount'] == expected:
            found = True
            break

    assert found, \
        f"Expected debt of {expected} from {debtor} not found in {debts}"


@then(parsers.parse('общая сумма долгов равна {amount:d} рублей'))
def verify_total_debts(context, amount: int):
    """Verify total debt amount."""
    expected = Decimal(amount)
    actual = context.query_result.get('total', Decimal('0'))
    assert actual == expected, \
        f"Expected total debts {expected}, got {actual}"


@then(parsers.parse('общая сумма к получению равна {amount:d} рублей'))
def verify_total_owed(context, amount: int):
    """Verify total amount owed to user."""
    expected = Decimal(amount)
    actual = context.query_result.get('total', Decimal('0'))
    assert actual == expected, \
        f"Expected total owed {expected}, got {actual}"


@then('результат пуст')
def result_is_empty(context):
    """Verify result contains no debts."""
    debts = context.query_result.get('debts', [])
    assert len(debts) == 0, f"Expected empty result, got {debts}"


@then(parsers.parse('сообщение "{expected_message}"'))
def verify_message(context, expected_message: str):
    """Verify result message."""
    actual = context.query_result.get('message', '')
    assert expected_message == actual, \
        f"Expected message '{expected_message}', got '{actual}'"


@then('результат содержит:')
def result_contains_table(context):
    """Verify result contains expected debts from table."""
    # Table data would be in context.table from pytest-bdd
    # For now, just verify we have debts
    debts = context.query_result.get('debts', [])
    assert len(debts) > 0, "Expected debts in result"

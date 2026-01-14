"""
Step definitions for payment processing scenarios.

Tests verify that payments correctly reduce debts.
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from decimal import Decimal

# Load scenarios
scenarios('../features/payment_processing.feature')


# ---------------------------------------------------------------------------
# GIVEN steps (Background)
# ---------------------------------------------------------------------------

@given(parsers.parse('order "{description}" for {amount:d} rubles is created with payer "{payer}" and participants "{participants}"'))
def setup_order_background(context, order_service, debt_service, description: str, amount: int, payer: str, participants: str):
    """Background: Create order and debts for payment tests."""
    participant_list = [p.strip().strip('"') for p in participants.split(',')]

    context.order = order_service.create_order(
        description=description,
        amount=Decimal(amount),
        payer=payer,
        participants=participant_list
    )

    context.debts = debt_service.create_debts_from_order(context.order)
    return context


@given(parsers.parse('"{debtor}" owes "{creditor}" {amount:d} rubles'))
def verify_initial_debt(context, debt_service, debtor: str, creditor: str, amount: int):
    """Verify initial debt state (precondition check)."""
    actual = debt_service.get_debt(debtor, creditor)
    expected = Decimal(amount)
    assert actual == expected, \
        f"Precondition failed: Expected {debtor} to owe {creditor} {expected}, got {actual}"
    return True


@given(parsers.parse('"{user}" does not owe "{creditor}" anything'))
def verify_no_initial_debt(context, debt_service, user: str, creditor: str):
    """Verify no debt exists (precondition check)."""
    actual = debt_service.get_debt(user, creditor)
    assert actual == Decimal('0'), \
        f"Precondition failed: Expected no debt from {user} to {creditor}, got {actual}"


# ---------------------------------------------------------------------------
# WHEN steps
# ---------------------------------------------------------------------------

@when(parsers.parse('"{debtor}" pays "{creditor}" {amount:d} rubles'))
def make_payment(context, payment_service, debtor: str, creditor: str, amount: int):
    """Make a payment from debtor to creditor."""
    try:
        context.payment = payment_service.record_payment(
            debtor=debtor,
            creditor=creditor,
            amount=Decimal(amount)
        )
        context.error = None
    except Exception as e:
        context.payment = None
        context.error = e


@when(parsers.parse('"{debtor}" tries to pay "{creditor}" {amount:d} rubles'))
def attempt_payment(context, payment_service, debtor: str, creditor: str, amount: int):
    """Attempt a payment that may fail."""
    try:
        context.payment = payment_service.record_payment(
            debtor=debtor,
            creditor=creditor,
            amount=Decimal(amount)
        )
        context.error = None
    except Exception as e:
        context.payment = None
        context.error = e


# ---------------------------------------------------------------------------
# THEN steps
# ---------------------------------------------------------------------------

@then('payment is recorded successfully')
def payment_recorded(context):
    """Verify payment was recorded successfully."""
    assert context.error is None, f"Expected no error, got: {context.error}"
    assert context.payment is not None, "Payment should be recorded"


@then(parsers.parse('"{debtor}" owes "{creditor}" {amount:d} rubles'))
def verify_remaining_debt(context, debt_service, debtor: str, creditor: str, amount: int):
    """Verify remaining debt after payment."""
    actual = debt_service.get_debt(debtor, creditor)
    expected = Decimal(amount)
    assert actual == expected, \
        f"Expected {debtor} to owe {creditor} {expected}, got {actual}"


@then(parsers.parse('debt of "{debtor}" to "{creditor}" remains {amount:d} rubles'))
def verify_debt_unchanged(context, debt_service, debtor: str, creditor: str, amount: int):
    """Verify debt remains unchanged after failed payment."""
    actual = debt_service.get_debt(debtor, creditor)
    expected = Decimal(amount)
    assert actual == expected, \
        f"Expected debt to remain {expected}, got {actual}"


@then(parsers.parse('error "{expected_message}" occurs'))
def verify_payment_error(context, expected_message: str):
    """Verify expected error message."""
    assert context.error is not None, "Expected an error but none occurred"
    assert expected_message in str(context.error), \
        f"Expected error containing '{expected_message}', got: {context.error}"

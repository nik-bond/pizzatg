"""
Step definitions for order creation scenarios.

These steps call REAL domain code - no mocks of business logic.
Tests will FAIL until domain implementation exists.
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from decimal import Decimal

# Load all scenarios from feature file
scenarios('../features/order_creation.feature')


# ---------------------------------------------------------------------------
# GIVEN steps
# ---------------------------------------------------------------------------

@given(parsers.parse('user "{username}" is the payer'))
def set_payer(context, username: str):
    """Set the payer for the order."""
    context.payer = username


# ---------------------------------------------------------------------------
# WHEN steps
# ---------------------------------------------------------------------------

@when(parsers.parse('order "{description}" is created for {amount:d} rubles'))
def create_order_with_amount(context, description: str, amount: int):
    """
    Attempt to create an order with given description and amount.
    Stores result or error in context for later assertions.
    """
    context.description = description
    context.amount = Decimal(amount)


@when(parsers.parse('participants are "{participants}"'))
def set_participants_and_execute(context, order_service, participants: str):
    """
    Set participants and execute order creation.
    This is where the actual domain logic is called.
    """
    # Parse participants from comma-separated string
    context.participants = [p.strip().strip('"') for p in participants.split(',')]

    try:
        # REAL domain call - calls actual implementation
        context.order = order_service.create_order(
            description=context.description,
            amount=context.amount,
            payer=context.payer,
            participants=context.participants
        )
        context.error = None
    except Exception as e:
        context.order = None
        context.error = e


@when('participants list is empty')
def set_no_participants_and_execute(context, order_service):
    """Execute order creation with empty participants list."""
    context.participants = []

    try:
        context.order = order_service.create_order(
            description=context.description,
            amount=context.amount,
            payer=context.payer,
            participants=context.participants
        )
        context.error = None
    except Exception as e:
        context.order = None
        context.error = e


# ---------------------------------------------------------------------------
# THEN steps
# ---------------------------------------------------------------------------

@then('order is successfully created')
def order_created_successfully(context):
    """Verify order was created without errors."""
    assert context.error is None, f"Expected no error, got: {context.error}"
    assert context.order is not None, "Order should be created"


@then(parsers.parse('per person amount is {expected:f} rubles'))
def verify_per_person_amount(context, expected: float):
    """Verify the calculated per-person share."""
    expected_decimal = Decimal(str(expected))
    actual = context.order.per_person_amount

    # Allow small rounding difference (0.01)
    assert abs(actual - expected_decimal) <= Decimal('0.01'), \
        f"Expected {expected_decimal} per person, got {actual}"


@then(parsers.parse('error "{expected_message}" occurs'))
def verify_error_message(context, expected_message: str):
    """Verify that the expected error was raised."""
    assert context.error is not None, "Expected an error but none occurred"
    assert expected_message in str(context.error), \
        f"Expected error containing '{expected_message}', got: {context.error}"


@then('order is not created')
def order_not_created(context):
    """Verify order was not created due to error."""
    assert context.order is None, "Order should not be created when there's an error"


@then(parsers.parse('"{username}" is included in participants'))
def verify_participant_included(context, username: str):
    """Verify that the specified user is in the participants list."""
    assert username in context.order.participants, \
        f"Expected '{username}' in participants, got: {context.order.participants}"

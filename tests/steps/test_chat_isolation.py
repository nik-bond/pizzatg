"""
BDD step definitions for chat isolation.

Tests that different Telegram groups have isolated data.
"""
import pytest
from decimal import Decimal
from pytest_bdd import scenarios, given, when, then, parsers

from src.domain.services import OrderService, DebtService, PaymentService
from src.domain.exceptions import DomainError


# Load all scenarios from the feature file
scenarios('../features/chat_isolation.feature')


# -------------------------------------------------------------------------
# Given steps - Setup
# -------------------------------------------------------------------------

@given('a fresh repository')
def fresh_repository(repository):
    """Repository is already fresh from fixture."""
    pass


@given('the order service')
def setup_order_service(order_service):
    """Order service is already available from fixture."""
    pass


@given('the debt service')
def setup_debt_service(debt_service):
    """Debt service is already available from fixture."""
    pass


@given(parsers.parse('user "{user}" creates order "{description}" for {amount:d} rubles with participants "{participants}" in chat {chat_id:d}'))
def given_create_order_in_chat(order_service, debt_service, user, description, amount, participants, chat_id):
    """Create an order in a specific chat (background step)."""
    participant_list = participants.split(',')
    order = order_service.create_order(
        description=description,
        amount=Decimal(amount),
        payer=user,
        participants=participant_list,
        created_by=user,
        chat_id=chat_id
    )
    # Create debts from the order
    debt_service.create_debts_from_order(order)


# -------------------------------------------------------------------------
# When steps - Actions
# -------------------------------------------------------------------------

@when(parsers.parse('user "{user}" creates order "{description}" for {amount:d} rubles with participants "{participants}" in chat {chat_id:d}'))
def create_order_in_chat(order_service, debt_service, user, description, amount, participants, chat_id):
    """Create an order in a specific chat."""
    participant_list = participants.split(',')
    order = order_service.create_order(
        description=description,
        amount=Decimal(amount),
        payer=user,
        participants=participant_list,
        created_by=user,
        chat_id=chat_id
    )
    # Create debts from the order
    debt_service.create_debts_from_order(order)


@when(parsers.parse('user "{debtor}" pays "{creditor}" {amount:d} rubles in chat {chat_id:d}'))
def record_payment_in_chat(payment_service, debtor, creditor, amount, chat_id):
    """Record a payment in a specific chat."""
    payment_service.record_payment(
        debtor=debtor,
        creditor=creditor,
        amount=Decimal(amount),
        chat_id=chat_id
    )


@when(parsers.parse('querying all debts in chat {chat_id:d}'))
def query_all_debts_in_chat(debt_service, chat_id, context):
    """Query all debts in a specific chat."""
    context['all_debts'] = debt_service.get_all_debts(chat_id)


# -------------------------------------------------------------------------
# Then steps - Assertions
# -------------------------------------------------------------------------

@then(parsers.parse('there should be {count:d} order in chat {chat_id:d}'))
@then(parsers.parse('there should be {count:d} orders in chat {chat_id:d}'))
def verify_order_count_in_chat(repository, count, chat_id):
    """Verify number of orders in a specific chat."""
    orders = repository.get_all_orders(chat_id)
    assert len(orders) == count, f"Expected {count} orders in chat {chat_id}, got {len(orders)}"


@then(parsers.parse('the last order in chat {chat_id:d} has description "{description}"'))
def verify_last_order_description_in_chat(repository, chat_id, description):
    """Verify the last order's description in a specific chat."""
    orders = repository.get_all_orders(chat_id)
    assert len(orders) > 0, f"No orders found in chat {chat_id}"
    # Get the most recent order
    last_order = sorted(orders, key=lambda o: o.created_at, reverse=True)[0]
    assert last_order.description == description, f"Expected '{description}', got '{last_order.description}'"


@then(parsers.parse('user "{user}" owes {amount:d} rubles in chat {chat_id:d}'))
def verify_user_owes_in_chat(debt_service, user, amount, chat_id):
    """Verify total amount user owes in a specific chat."""
    result = debt_service.get_debts_by_user(user, chat_id)
    total = result['total']
    assert total == Decimal(amount), f"Expected {user} to owe {amount} in chat {chat_id}, got {total}"


@then(parsers.parse('user "{user}" has net debt {amount:d} rubles to "{creditor}" in chat {chat_id:d}'))
def verify_net_debt_in_chat(debt_service, user, amount, creditor, chat_id):
    """Verify net debt between two users in a specific chat."""
    result = debt_service.get_consolidated_debts(user, chat_id)
    debts = result.get('debts', [])
    
    # Find the debt to this creditor
    debt_to_creditor = None
    for debt_info in debts:
        if debt_info['counterparty'] == creditor:
            debt_to_creditor = debt_info
            break
    
    if amount == 0:
        assert debt_to_creditor is None or debt_to_creditor['net_direction'] == 'settled', \
            f"Expected no debt to {creditor}, got {debt_to_creditor}"
    elif amount < 0:
        # Negative debt means user is owed money
        expected = Decimal(-amount)
        assert debt_to_creditor is not None, f"Expected debt from {creditor}, found none"
        assert debt_to_creditor['net_direction'] == 'they_owe', \
            f"Expected {creditor} to owe {expected}, but direction is {debt_to_creditor['net_direction']}"
        assert debt_to_creditor['net_amount'] == expected, \
            f"Expected {expected} from {creditor}, got {debt_to_creditor['net_amount']}"
    else:
        # Positive debt means user owes money
        expected = Decimal(amount)
        assert debt_to_creditor is not None, f"Expected debt to {creditor}, found none"
        assert debt_to_creditor['net_direction'] == 'i_owe', \
            f"Expected to owe {creditor} {expected}, but direction is {debt_to_creditor['net_direction']}"
        assert debt_to_creditor['net_amount'] == expected, \
            f"Expected {expected} to {creditor}, got {debt_to_creditor['net_amount']}"


@then(parsers.parse('there are {count:d} debt records'))
@then(parsers.parse('there are {count:d} debt record'))
def verify_debt_count(context, count):
    """Verify number of debt records from previous query."""
    result = context.get('all_debts', {})
    debts = result.get('debts', [])
    assert len(debts) == count, f"Expected {count} debt records, got {len(debts)}"

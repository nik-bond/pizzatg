"""
Step definitions for persistence (SQLite) integration tests.

These tests verify data survives restarts and concurrent access is safe.
"""
import os
import tempfile
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor

from src.persistence.sqlite_repo import SQLiteRepository
from src.domain.services import OrderService, DebtService, PaymentService

# Load scenarios
scenarios('../features/persistence.feature')


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_path():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def sqlite_repo(db_path):
    """SQLite repository for testing."""
    return SQLiteRepository(db_path)


@pytest.fixture
def sqlite_order_service(sqlite_repo):
    """OrderService with SQLite repository."""
    return OrderService(sqlite_repo)


@pytest.fixture
def sqlite_debt_service(sqlite_repo):
    """DebtService with SQLite repository."""
    return DebtService(sqlite_repo)


@pytest.fixture
def sqlite_payment_service(sqlite_repo):
    """PaymentService with SQLite repository."""
    return PaymentService(sqlite_repo)


@pytest.fixture
def persistence_context():
    """Context for persistence tests."""
    class Context:
        def __init__(self):
            self.db_path = None
            self.order = None
            self.orders = []
            self.debts = []
            self.error = None

    return Context()


# ---------------------------------------------------------------------------
# GIVEN steps
# ---------------------------------------------------------------------------

@given('a fresh SQLite database')
def fresh_database(persistence_context, db_path, sqlite_repo):
    """Initialize a fresh SQLite database."""
    persistence_context.db_path = db_path
    persistence_context.repo = sqlite_repo
    return persistence_context


@given(parsers.parse('order "{description}" for {amount:d} rubles is created with payer "{payer}" and participants "{participants}"'))
def create_order_sqlite(persistence_context, sqlite_order_service, description: str, amount: int, payer: str, participants: str):
    """Create an order in SQLite."""
    participant_list = [p.strip().strip('"') for p in participants.split(',')]

    persistence_context.order = sqlite_order_service.create_order(
        description=description,
        amount=Decimal(amount),
        payer=payer,
        participants=participant_list
    )
    persistence_context.orders.append(persistence_context.order)


@given('debts are generated from the order')
def generate_debts_sqlite(persistence_context, sqlite_debt_service):
    """Generate debts from the last created order."""
    debts = sqlite_debt_service.create_debts_from_order(persistence_context.order)
    persistence_context.debts.extend(debts)


@given(parsers.parse('"{debtor}" pays "{creditor}" {amount:d} rubles'))
def make_payment_sqlite(persistence_context, sqlite_payment_service, debtor: str, creditor: str, amount: int):
    """Make a payment in SQLite."""
    sqlite_payment_service.record_payment(
        debtor=debtor,
        creditor=creditor,
        amount=Decimal(amount)
    )


# ---------------------------------------------------------------------------
# WHEN steps
# ---------------------------------------------------------------------------

@when('the repository is reopened')
def reopen_repository(persistence_context):
    """Simulate restart by creating new repository instance."""
    # Create a new repository pointing to the same database
    persistence_context.repo = SQLiteRepository(persistence_context.db_path)


@when(parsers.parse('"{user1}" and "{user2}" pay simultaneously'))
def simultaneous_payments(persistence_context, user1: str, user2: str):
    """Simulate concurrent payments."""
    def make_payment(debtor):
        repo = SQLiteRepository(persistence_context.db_path)
        payment_service = PaymentService(repo)
        debt_service = DebtService(repo)

        # Get current debt
        current_debt = debt_service.get_debt(debtor, "ivan")
        if current_debt > 0:
            payment_service.record_payment(
                debtor=debtor,
                creditor="ivan",
                amount=min(Decimal('500'), current_debt)
            )

    # Execute payments in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(make_payment, user1),
            executor.submit(make_payment, user2)
        ]
        # Wait for completion and check for errors
        for future in futures:
            try:
                future.result()
            except Exception as e:
                persistence_context.error = e


# ---------------------------------------------------------------------------
# THEN steps
# ---------------------------------------------------------------------------

@then(parsers.parse('order "{description}" still exists'))
def verify_order_exists(persistence_context, description: str):
    """Verify order persists after reopen."""
    # Find the order we created
    orders = persistence_context.repo.get_all_orders()
    matching = [o for o in orders if o.description == description]
    assert len(matching) > 0, f"Order '{description}' not found after reopen"
    persistence_context.order = matching[0]


@then(parsers.parse('order has amount {amount:d} rubles'))
def verify_order_amount(persistence_context, amount: int):
    """Verify order amount."""
    assert persistence_context.order.amount == Decimal(amount), \
        f"Expected amount {amount}, got {persistence_context.order.amount}"


@then(parsers.parse('"{debtor}" still owes "{creditor}" {amount:d} rubles'))
def verify_debt_persists(persistence_context, debtor: str, creditor: str, amount: int):
    """Verify debt persists after reopen."""
    debt_service = DebtService(persistence_context.repo)
    actual = debt_service.get_debt(debtor, creditor)
    expected = Decimal(amount)
    assert actual == expected, \
        f"Expected {debtor} to owe {creditor} {expected}, got {actual}"


@then(parsers.parse('"{debtor}" owes "{creditor}" {amount:d} rubles'))
def verify_debt_amount(persistence_context, debtor: str, creditor: str, amount: int):
    """Verify debt amount."""
    debt_service = DebtService(persistence_context.repo)
    actual = debt_service.get_debt(debtor, creditor)
    expected = Decimal(amount)
    assert actual == expected, \
        f"Expected {debtor} to owe {creditor} {expected}, got {actual}"


@then('both payments are recorded correctly')
def verify_both_payments(persistence_context):
    """Verify concurrent payments succeeded."""
    assert persistence_context.error is None, \
        f"Concurrent payment failed: {persistence_context.error}"


@then('no data corruption occurs')
def verify_no_corruption(persistence_context):
    """Verify database integrity after concurrent access."""
    debt_service = DebtService(persistence_context.repo)

    # Get all debts and verify they make sense
    all_debts = debt_service.get_all_debts()

    for debt_info in all_debts['debts']:
        # Amount should be non-negative
        assert debt_info['amount'] >= Decimal('0'), \
            f"Negative debt found: {debt_info}"

    # No exception means integrity is maintained
    assert True

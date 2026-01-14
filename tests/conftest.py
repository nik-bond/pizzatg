"""
Pytest configuration and shared fixtures.

This conftest provides fixtures for BDD tests that operate on
real domain logic - no mocks of business rules.
"""
import pytest
from decimal import Decimal

# These imports will fail until domain code is implemented
# This is intentional - tests must fail first (TDD)
from src.domain.services import OrderService, DebtService, PaymentService
from src.domain.models import Order, Debt, Payment
from src.persistence.memory_repo import InMemoryRepository


@pytest.fixture
def repository():
    """
    In-memory repository for testing.
    Uses real repository implementation, not mocks.
    """
    return InMemoryRepository()


@pytest.fixture
def order_service(repository):
    """OrderService with real repository."""
    return OrderService(repository)


@pytest.fixture
def debt_service(repository):
    """DebtService with real repository."""
    return DebtService(repository)


@pytest.fixture
def payment_service(repository):
    """PaymentService with real repository."""
    return PaymentService(repository)


@pytest.fixture
def context():
    """
    Shared context for BDD scenarios.
    Stores state between Given/When/Then steps.
    """
    class Context:
        def __init__(self):
            self.payer: str = None
            self.description: str = None
            self.amount: Decimal = None
            self.participants: list[str] = []
            self.order: Order = None
            self.error: Exception = None
            self.debts: list[Debt] = []
            self.payments: list[Payment] = []
            self.query_result: dict = None

    return Context()

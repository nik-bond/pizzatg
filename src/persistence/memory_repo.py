"""
In-memory repository implementation.

Used for testing without database dependencies.
Provides same interface as SQLite repository.
"""
from typing import Optional
from decimal import Decimal

from src.domain.models import Order, Debt, Payment


class InMemoryRepository:
    """
    In-memory implementation of Repository protocol.

    Stores all data in dictionaries - lost on restart.
    Ideal for fast, isolated unit tests.
    """

    def __init__(self):
        self._orders: dict[str, Order] = {}
        self._debts: dict[tuple[str, str, int], Debt] = {}  # (debtor, creditor, chat_id) -> Debt
        self._payments: list[Payment] = []
        self._users: set[str] = set()

    # -------------------------------------------------------------------------
    # Order operations
    # -------------------------------------------------------------------------

    def save_order(self, order: Order) -> None:
        """Save or update an order."""
        self._orders[order.id] = order
        # Auto-register participants as users
        for participant in order.participants:
            self._users.add(participant)

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self._orders.get(order_id)

    def get_all_orders(self) -> list[Order]:
        """Get all orders."""
        return list(self._orders.values())

    def delete_order(self, order_id: str) -> None:
        """Delete an order by ID."""
        if order_id in self._orders:
            del self._orders[order_id]

    # -------------------------------------------------------------------------
    # Debt operations
    # -------------------------------------------------------------------------

    def save_debt(self, debt: Debt) -> None:
        """Save or update a debt."""
        key = (debt.debtor, debt.creditor, debt.chat_id)
        self._debts[key] = debt

    def get_debt(self, debtor: str, creditor: str, chat_id: int = 0) -> Optional[Debt]:
        """Get debt between two users in a specific chat."""
        return self._debts.get((debtor, creditor, chat_id))

    def get_debts_by_debtor(self, debtor: str, chat_id: int = 0) -> list[Debt]:
        """Get all debts where user is debtor in a specific chat."""
        return [
            debt for (d, c, ch), debt in self._debts.items()
            if d == debtor and ch == chat_id
        ]

    def get_debts_by_creditor(self, creditor: str, chat_id: int = 0) -> list[Debt]:
        """Get all debts where user is creditor in a specific chat."""
        return [
            debt for (d, c, ch), debt in self._debts.items()
            if c == creditor and ch == chat_id
        ]

    def get_all_debts(self, chat_id: int = 0) -> list[Debt]:
        """Get all debts in a specific chat."""
        return [
            debt for (d, c, ch), debt in self._debts.items()
            if ch == chat_id
        ]

    def delete_debt(self, debtor: str, creditor: str, chat_id: int = 0) -> None:
        """Delete a debt (when fully paid)."""
        key = (debtor, creditor, chat_id)
        if key in self._debts:
            del self._debts[key]

    # -------------------------------------------------------------------------
    # Payment operations
    # -------------------------------------------------------------------------

    def save_payment(self, payment: Payment) -> None:
        """Save a payment record."""
        self._payments.append(payment)

    def get_payments_by_debtor(self, debtor: str, chat_id: int = 0) -> list[Payment]:
        """Get all payments made by user in a specific chat."""
        return [p for p in self._payments if p.debtor == debtor and p.chat_id == chat_id]

    def get_payments_by_creditor(self, creditor: str, chat_id: int = 0) -> list[Payment]:
        """Get all payments received by user in a specific chat."""
        return [p for p in self._payments if p.creditor == creditor and p.chat_id == chat_id]

    # -------------------------------------------------------------------------
    # User operations
    # -------------------------------------------------------------------------

    def add_user(self, username: str) -> None:
        """Register a user."""
        self._users.add(username)

    def user_exists(self, username: str) -> bool:
        """Check if user exists."""
        return username in self._users

    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------

    def clear(self) -> None:
        """Clear all data (for test reset)."""
        self._orders.clear()
        self._debts.clear()
        self._payments.clear()
        self._users.clear()

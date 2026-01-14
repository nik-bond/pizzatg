"""
SQLite repository implementation.

Persistent storage for orders, debts, and payments.
Implements the same Repository protocol as InMemoryRepository.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from src.domain.models import Order, Debt, Payment


class SQLiteRepository:
    """
    SQLite implementation of Repository protocol.

    Provides persistent storage with ACID guarantees.
    All queries use parameterized statements to prevent SQL injection.
    """

    def __init__(self, db_path: str = "debts.db"):
        """
        Initialize SQLite repository.

        Args:
            db_path: Path to SQLite database file.
                     Use ":memory:" for in-memory testing.
        """
        self._db_path = db_path
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with proper settings."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def _transaction(self):
        """Context manager for database transactions."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Initialize database schema if not exists."""
        with self._transaction() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    payer TEXT NOT NULL,
                    participants TEXT NOT NULL,
                    per_person_amount TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (payer) REFERENCES users(username)
                );

                CREATE TABLE IF NOT EXISTS debts (
                    debtor TEXT NOT NULL,
                    creditor TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (debtor, creditor),
                    FOREIGN KEY (debtor) REFERENCES users(username),
                    FOREIGN KEY (creditor) REFERENCES users(username)
                );

                CREATE TABLE IF NOT EXISTS payments (
                    id TEXT PRIMARY KEY,
                    debtor TEXT NOT NULL,
                    creditor TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (debtor) REFERENCES users(username),
                    FOREIGN KEY (creditor) REFERENCES users(username)
                );

                CREATE INDEX IF NOT EXISTS idx_debts_debtor ON debts(debtor);
                CREATE INDEX IF NOT EXISTS idx_debts_creditor ON debts(creditor);
                CREATE INDEX IF NOT EXISTS idx_orders_payer ON orders(payer);
            """)

    # -------------------------------------------------------------------------
    # User operations
    # -------------------------------------------------------------------------

    def add_user(self, username: str) -> None:
        """Register a user."""
        with self._transaction() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (username) VALUES (?)",
                (username,)
            )

    def user_exists(self, username: str) -> bool:
        """Check if user exists."""
        with self._transaction() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM users WHERE username = ?",
                (username,)
            )
            return cursor.fetchone() is not None

    def _ensure_user(self, conn: sqlite3.Connection, username: str) -> None:
        """Ensure user exists, creating if necessary."""
        conn.execute(
            "INSERT OR IGNORE INTO users (username) VALUES (?)",
            (username,)
        )

    # -------------------------------------------------------------------------
    # Order operations
    # -------------------------------------------------------------------------

    def save_order(self, order: Order) -> None:
        """Save or update an order."""
        with self._transaction() as conn:
            # Ensure all participants exist as users
            for participant in order.participants:
                self._ensure_user(conn, participant)

            # Store participants as comma-separated string
            participants_str = ",".join(order.participants)

            conn.execute("""
                INSERT OR REPLACE INTO orders
                (id, description, amount, payer, participants, per_person_amount, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                order.id,
                order.description,
                str(order.amount),
                order.payer,
                participants_str,
                str(order.per_person_amount),
                order.created_at.isoformat()
            ))

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        with self._transaction() as conn:
            cursor = conn.execute(
                "SELECT * FROM orders WHERE id = ?",
                (order_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return Order(
                id=row['id'],
                description=row['description'],
                amount=Decimal(row['amount']),
                payer=row['payer'],
                participants=row['participants'].split(','),
                per_person_amount=Decimal(row['per_person_amount']),
                created_at=datetime.fromisoformat(row['created_at'])
            )

    def get_all_orders(self) -> list[Order]:
        """Get all orders."""
        with self._transaction() as conn:
            cursor = conn.execute("SELECT * FROM orders ORDER BY created_at DESC")
            orders = []
            for row in cursor.fetchall():
                orders.append(Order(
                    id=row['id'],
                    description=row['description'],
                    amount=Decimal(row['amount']),
                    payer=row['payer'],
                    participants=row['participants'].split(','),
                    per_person_amount=Decimal(row['per_person_amount']),
                    created_at=datetime.fromisoformat(row['created_at'])
                ))
            return orders

    # -------------------------------------------------------------------------
    # Debt operations
    # -------------------------------------------------------------------------

    def save_debt(self, debt: Debt) -> None:
        """Save or update a debt."""
        with self._transaction() as conn:
            # Ensure both users exist
            self._ensure_user(conn, debt.debtor)
            self._ensure_user(conn, debt.creditor)

            conn.execute("""
                INSERT OR REPLACE INTO debts
                (debtor, creditor, amount, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                debt.debtor,
                debt.creditor,
                str(debt.amount),
                debt.created_at.isoformat(),
                debt.updated_at.isoformat()
            ))

    def get_debt(self, debtor: str, creditor: str) -> Optional[Debt]:
        """Get debt between two users."""
        with self._transaction() as conn:
            cursor = conn.execute(
                "SELECT * FROM debts WHERE debtor = ? AND creditor = ?",
                (debtor, creditor)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return Debt(
                debtor=row['debtor'],
                creditor=row['creditor'],
                amount=Decimal(row['amount']),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )

    def get_debts_by_debtor(self, debtor: str) -> list[Debt]:
        """Get all debts where user is debtor."""
        with self._transaction() as conn:
            cursor = conn.execute(
                "SELECT * FROM debts WHERE debtor = ?",
                (debtor,)
            )
            return [
                Debt(
                    debtor=row['debtor'],
                    creditor=row['creditor'],
                    amount=Decimal(row['amount']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                for row in cursor.fetchall()
            ]

    def get_debts_by_creditor(self, creditor: str) -> list[Debt]:
        """Get all debts where user is creditor."""
        with self._transaction() as conn:
            cursor = conn.execute(
                "SELECT * FROM debts WHERE creditor = ?",
                (creditor,)
            )
            return [
                Debt(
                    debtor=row['debtor'],
                    creditor=row['creditor'],
                    amount=Decimal(row['amount']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                for row in cursor.fetchall()
            ]

    def get_all_debts(self) -> list[Debt]:
        """Get all debts."""
        with self._transaction() as conn:
            cursor = conn.execute("SELECT * FROM debts")
            return [
                Debt(
                    debtor=row['debtor'],
                    creditor=row['creditor'],
                    amount=Decimal(row['amount']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                for row in cursor.fetchall()
            ]

    def delete_debt(self, debtor: str, creditor: str) -> None:
        """Delete a debt (when fully paid)."""
        with self._transaction() as conn:
            conn.execute(
                "DELETE FROM debts WHERE debtor = ? AND creditor = ?",
                (debtor, creditor)
            )

    # -------------------------------------------------------------------------
    # Payment operations
    # -------------------------------------------------------------------------

    def save_payment(self, payment: Payment) -> None:
        """Save a payment record."""
        with self._transaction() as conn:
            # Ensure both users exist
            self._ensure_user(conn, payment.debtor)
            self._ensure_user(conn, payment.creditor)

            conn.execute("""
                INSERT INTO payments (id, debtor, creditor, amount, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                payment.id,
                payment.debtor,
                payment.creditor,
                str(payment.amount),
                payment.created_at.isoformat()
            ))

    def get_payments_by_debtor(self, debtor: str) -> list[Payment]:
        """Get all payments made by user."""
        with self._transaction() as conn:
            cursor = conn.execute(
                "SELECT * FROM payments WHERE debtor = ? ORDER BY created_at DESC",
                (debtor,)
            )
            return [
                Payment(
                    id=row['id'],
                    debtor=row['debtor'],
                    creditor=row['creditor'],
                    amount=Decimal(row['amount']),
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                for row in cursor.fetchall()
            ]

    def get_payments_by_creditor(self, creditor: str) -> list[Payment]:
        """Get all payments received by user."""
        with self._transaction() as conn:
            cursor = conn.execute(
                "SELECT * FROM payments WHERE creditor = ? ORDER BY created_at DESC",
                (creditor,)
            )
            return [
                Payment(
                    id=row['id'],
                    debtor=row['debtor'],
                    creditor=row['creditor'],
                    amount=Decimal(row['amount']),
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                for row in cursor.fetchall()
            ]

    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------

    def clear(self) -> None:
        """Clear all data (for testing)."""
        with self._transaction() as conn:
            conn.execute("DELETE FROM payments")
            conn.execute("DELETE FROM debts")
            conn.execute("DELETE FROM orders")
            conn.execute("DELETE FROM users")

"""
Domain models.

Pure data classes representing core domain concepts.
No business logic here - just data and basic validation.
"""
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from typing import Optional
import uuid


# Constants for validation
MAX_AMOUNT = Decimal('1_000_000_000')  # 1 billion rubles
MIN_PARTICIPANTS = 2


@dataclass
class Order:
    """
    Represents a shared expense order.

    Attributes:
        id: Unique identifier
        description: What was ordered (e.g., "пицца")
        amount: Total amount in rubles
        payer: Username of person who paid
        participants: List of usernames sharing the cost
        per_person_amount: Calculated share per participant
        created_at: When order was created
    """
    id: str
    description: str
    amount: Decimal
    payer: str
    participants: list[str]
    per_person_amount: Decimal
    created_at: datetime = field(default_factory=datetime.now)

    @staticmethod
    def calculate_per_person(amount: Decimal, num_participants: int) -> Decimal:
        """
        Calculate per-person share with proper rounding.

        Uses ROUND_HALF_UP to 2 decimal places.
        """
        if num_participants <= 0:
            raise ValueError("Number of participants must be positive")

        share = amount / num_participants
        return share.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def generate_id() -> str:
        """Generate unique order ID."""
        return str(uuid.uuid4())[:8]


@dataclass
class Debt:
    """
    Represents a debt from one user to another.

    Attributes:
        debtor: Username who owes money
        creditor: Username who is owed money
        amount: How much is owed
        created_at: When debt was first created
        updated_at: When debt was last modified
    """
    debtor: str
    creditor: str
    amount: Decimal
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def reduce(self, payment_amount: Decimal) -> 'Debt':
        """
        Create new Debt with reduced amount after payment.

        Returns new Debt instance (immutable pattern).
        """
        new_amount = self.amount - payment_amount
        return Debt(
            debtor=self.debtor,
            creditor=self.creditor,
            amount=new_amount,
            created_at=self.created_at,
            updated_at=datetime.now()
        )

    @property
    def is_settled(self) -> bool:
        """Check if debt is fully paid off."""
        return self.amount <= Decimal('0')


@dataclass
class Payment:
    """
    Represents a payment from debtor to creditor.

    Attributes:
        id: Unique identifier
        debtor: Username who paid
        creditor: Username who received
        amount: Amount paid
        created_at: When payment was made
    """
    id: str
    debtor: str
    creditor: str
    amount: Decimal
    created_at: datetime = field(default_factory=datetime.now)

    @staticmethod
    def generate_id() -> str:
        """Generate unique payment ID."""
        return str(uuid.uuid4())[:8]

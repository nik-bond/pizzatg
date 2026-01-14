"""
Domain services.

Business logic for order management, debt tracking, and payments.
Services coordinate between models and repositories.
"""
from decimal import Decimal
from typing import Protocol, Optional

from .models import Order, Debt, Payment, MAX_AMOUNT, MIN_PARTICIPANTS
from .exceptions import (
    ValidationError,
    DebtNotFoundError,
    PaymentExceedsDebtError,
)


class Repository(Protocol):
    """Repository interface for persistence."""

    def save_order(self, order: Order) -> None: ...
    def get_order(self, order_id: str) -> Optional[Order]: ...

    def save_debt(self, debt: Debt) -> None: ...
    def get_debt(self, debtor: str, creditor: str) -> Optional[Debt]: ...
    def get_debts_by_debtor(self, debtor: str) -> list[Debt]: ...
    def get_debts_by_creditor(self, creditor: str) -> list[Debt]: ...
    def get_all_debts(self) -> list[Debt]: ...
    def delete_debt(self, debtor: str, creditor: str) -> None: ...

    def save_payment(self, payment: Payment) -> None: ...

    def add_user(self, username: str) -> None: ...
    def user_exists(self, username: str) -> bool: ...


class OrderService:
    """
    Service for creating and managing orders.

    Handles validation and order creation.
    Does NOT create debts - that's DebtService's responsibility.
    """

    def __init__(self, repository: Repository):
        self._repo = repository

    def create_order(
        self,
        description: str,
        amount: Decimal,
        payer: str,
        participants: list[str]
    ) -> Order:
        """
        Create a new order with validation.

        Args:
            description: What was ordered
            amount: Total amount in rubles
            payer: Username who paid
            participants: List of usernames sharing the cost

        Returns:
            Created Order instance

        Raises:
            ValidationError: If validation fails
        """
        # Validate amount
        self._validate_amount(amount)

        # Ensure payer is in participants
        if payer not in participants:
            participants = [payer] + participants

        # Validate participants
        self._validate_participants(participants)

        # Calculate per-person amount
        per_person = Order.calculate_per_person(amount, len(participants))

        # Create order
        order = Order(
            id=Order.generate_id(),
            description=description or "без описания",
            amount=amount,
            payer=payer,
            participants=participants,
            per_person_amount=per_person
        )

        # Save to repository
        self._repo.save_order(order)

        return order

    def _validate_amount(self, amount: Decimal) -> None:
        """Validate order amount."""
        if amount <= Decimal('0'):
            raise ValidationError("Сумма должна быть положительной")

        if amount > MAX_AMOUNT:
            raise ValidationError("Сумма превышает допустимый лимит")

    def _validate_participants(self, participants: list[str]) -> None:
        """Validate participants list."""
        if len(participants) < MIN_PARTICIPANTS:
            raise ValidationError("Требуется минимум два участника")


class DebtService:
    """
    Service for managing debts.

    Handles debt creation, updates, and queries.
    """

    def __init__(self, repository: Repository):
        self._repo = repository

    def create_debts_from_order(self, order: Order) -> list[Debt]:
        """
        Create debts from an order.

        Each participant (except payer) owes the payer their share.

        Args:
            order: The order to create debts from

        Returns:
            List of created Debt instances
        """
        debts = []

        for participant in order.participants:
            # Payer doesn't owe themselves
            if participant == order.payer:
                continue

            # Check if debt already exists
            existing = self._repo.get_debt(participant, order.payer)

            if existing:
                # Add to existing debt, accumulate descriptions
                descriptions = [existing.description, order.description] if existing.description else [order.description]
                combined_description = ", ".join(d for d in descriptions if d)
                new_debt = Debt(
                    debtor=participant,
                    creditor=order.payer,
                    amount=existing.amount + order.per_person_amount,
                    description=combined_description,
                    created_at=existing.created_at
                )
            else:
                # Create new debt
                new_debt = Debt(
                    debtor=participant,
                    creditor=order.payer,
                    amount=order.per_person_amount,
                    description=order.description
                )

            self._repo.save_debt(new_debt)
            debts.append(new_debt)

        return debts

    def get_debt(self, debtor: str, creditor: str) -> Decimal:
        """
        Get debt amount between two users.

        Returns Decimal('0') if no debt exists.
        """
        debt = self._repo.get_debt(debtor, creditor)
        return debt.amount if debt else Decimal('0')

    def get_total_owed_by(self, user: str) -> Decimal:
        """Get total amount user owes to others."""
        debts = self._repo.get_debts_by_debtor(user)
        return sum((d.amount for d in debts), Decimal('0'))

    def get_total_owed_to(self, user: str) -> Decimal:
        """Get total amount others owe to user."""
        debts = self._repo.get_debts_by_creditor(user)
        return sum((d.amount for d in debts), Decimal('0'))

    def get_debts_by_user(self, user: str) -> dict:
        """
        Get all debts owed BY user.

        Returns dict with 'debts', 'total', and 'message' keys.
        """
        debts = self._repo.get_debts_by_debtor(user)

        # Filter out settled debts
        active_debts = [d for d in debts if not d.is_settled]

        if not active_debts:
            return {
                'debts': [],
                'total': Decimal('0'),
                'message': 'Долгов нет'
            }

        return {
            'debts': [
                {'creditor': d.creditor, 'amount': d.amount, 'description': d.description}
                for d in active_debts
            ],
            'total': sum((d.amount for d in active_debts), Decimal('0')),
            'message': None
        }

    def get_debts_to_user(self, user: str) -> dict:
        """
        Get all debts owed TO user.

        Returns dict with 'debts', 'total', and 'message' keys.
        """
        debts = self._repo.get_debts_by_creditor(user)

        # Filter out settled debts
        active_debts = [d for d in debts if not d.is_settled]

        if not active_debts:
            return {
                'debts': [],
                'total': Decimal('0'),
                'message': 'Вам никто не должен'
            }

        return {
            'debts': [
                {'debtor': d.debtor, 'amount': d.amount, 'description': d.description}
                for d in active_debts
            ],
            'total': sum((d.amount for d in active_debts), Decimal('0')),
            'message': None
        }

    def get_all_debts(self) -> dict:
        """
        Get all debts in the system.

        Returns dict with 'debts' and 'total' keys.
        """
        debts = self._repo.get_all_debts()

        # Filter out settled debts
        active_debts = [d for d in debts if not d.is_settled]

        return {
            'debts': [
                {
                    'debtor': d.debtor,
                    'creditor': d.creditor,
                    'amount': d.amount,
                    'description': d.description
                }
                for d in active_debts
            ],
            'total': sum((d.amount for d in active_debts), Decimal('0'))
        }

    def get_net_balance(self, user1: str, user2: str) -> dict:
        """
        Calculate net balance between two users.

        Returns dict with net_balance, net_debtor, net_creditor.
        """
        debt_1_to_2 = self.get_debt(user1, user2)
        debt_2_to_1 = self.get_debt(user2, user1)

        net = debt_1_to_2 - debt_2_to_1

        if net > 0:
            return {
                'net_balance': net,
                'net_debtor': user1,
                'net_creditor': user2
            }
        elif net < 0:
            return {
                'net_balance': abs(net),
                'net_debtor': user2,
                'net_creditor': user1
            }
        else:
            return {
                'net_balance': Decimal('0'),
                'net_debtor': None,
                'net_creditor': None
            }

    def reduce_debt(self, debtor: str, creditor: str, amount: Decimal) -> Debt:
        """
        Reduce debt by payment amount.

        Returns updated Debt instance.

        Raises:
            DebtNotFoundError: If no debt exists
            PaymentExceedsDebtError: If amount > debt
        """
        debt = self._repo.get_debt(debtor, creditor)

        if not debt or debt.is_settled:
            raise DebtNotFoundError(f"Долг не найден")

        if amount > debt.amount:
            raise PaymentExceedsDebtError(
                f"Сумма платежа превышает долг"
            )

        new_debt = debt.reduce(amount)

        if new_debt.is_settled:
            self._repo.delete_debt(debtor, creditor)
        else:
            self._repo.save_debt(new_debt)

        return new_debt


class PaymentService:
    """
    Service for recording payments.

    Coordinates between debt reduction and payment recording.
    """

    def __init__(self, repository: Repository):
        self._repo = repository
        self._debt_service = DebtService(repository)

    def record_payment(
        self,
        debtor: str,
        creditor: str,
        amount: Decimal
    ) -> Payment:
        """
        Record a payment from debtor to creditor.

        Args:
            debtor: Username who is paying
            creditor: Username receiving payment
            amount: Amount being paid

        Returns:
            Created Payment instance

        Raises:
            ValidationError: If amount is invalid
            DebtNotFoundError: If no debt exists
            PaymentExceedsDebtError: If amount > debt
        """
        # Validate amount
        if amount <= Decimal('0'):
            raise ValidationError("Сумма платежа должна быть положительной")

        # Reduce debt (will raise if invalid)
        self._debt_service.reduce_debt(debtor, creditor, amount)

        # Create payment record
        payment = Payment(
            id=Payment.generate_id(),
            debtor=debtor,
            creditor=creditor,
            amount=amount
        )

        self._repo.save_payment(payment)

        return payment

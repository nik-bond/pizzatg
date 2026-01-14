"""
Domain exceptions.

Custom exceptions for domain validation and business rule violations.
These exceptions are caught by handlers and converted to user-friendly messages.
"""


class DomainError(Exception):
    """Base class for domain exceptions."""
    pass


class ValidationError(DomainError):
    """
    Raised when input validation fails.

    Examples:
    - Negative or zero amount
    - Amount exceeds limit
    - Not enough participants
    """
    pass


class DebtNotFoundError(DomainError):
    """
    Raised when attempting to operate on a non-existent debt.

    Example: Paying someone you don't owe money to.
    """
    pass


class PaymentExceedsDebtError(DomainError):
    """
    Raised when payment amount exceeds the outstanding debt.

    This prevents overpayment which would create reverse debt.
    """
    pass


class OrderNotFoundError(DomainError):
    """Raised when referencing a non-existent order."""
    pass


class UserNotFoundError(DomainError):
    """Raised when referencing a non-existent user."""
    pass

class PaymentError(Exception):
    """Base class for all payment system errors"""


class InsufficientFundsError(PaymentError):
    """Raised when a user lacks sufficient funds"""


class UserNotFoundError(PaymentError):
    """Raised when a user doesn't exist"""


class TransactionError(PaymentError):
    """Base class for transaction-related errors"""


class SameRecipientError(PaymentError):
    """Raised when it is the same recipient as sender."""


class NegativeAmountError(PaymentError):
    """Raised when negative amount sent."""

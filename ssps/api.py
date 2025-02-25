import logging

from typing import Optional
from datetime import datetime

from ssps.core.engine import PaymentEngine
from ssps.core.exceptions import (
    InsufficientFundsError,
    UserNotFoundError,
    PaymentError,
    SameRecipientError, NegativeAmountError,
)

logger = logging.getLogger(__name__)

# Singleton engine instance
_engine: Optional[PaymentEngine] = None


def initialize(db_adapter) -> None:
    """Initialize the payment system with a database adapter"""
    global _engine
    _engine = PaymentEngine(db_adapter)

    logger.info(
        f"Initialized PaymentEngine with DB adapter: {db_adapter.__class__.__name__}"
    )


def transfer(sender_id: str, recipient_id: str, amount: float) -> bool:
    """
    Transfer funds between users

    Args:
        sender_id: Unique identifier of the sender
        recipient_id: Unique identifier of the recipient
        amount: Positive amount to transfer

    Returns:
        bool: True if transfer succeeded

    Raises:
        PaymentError: Base class for all payment exceptions
        RuntimeError: If system not initialized
    """
    if _engine.db is None:
        raise RuntimeError(
            "Payment system not initialized or wrongly configured. Call initialize() first."
        )

    try:
        return _engine.transfer(sender_id, recipient_id, amount)
    except (InsufficientFundsError, UserNotFoundError, SameRecipientError, NegativeAmountError) as e:
        raise PaymentError(f"Transfer failed: {str(e)}") from e
    except Exception as e:
        raise PaymentError("An unexpected error occurred during the transfer.") from e


def check_balance(user_id: str) -> float:
    """
    Get current balance for a user

    Args:
        user_id: Unique user identifier

    Returns:
        float: Current balance

    Raises:
        RuntimeError: If system not initialized
    """
    if _engine.db is None:
        raise RuntimeError("Payment system not initialized. Call initialize() first.")

    return _engine.get_balance(user_id)


def get_transaction_history(
    user_id: str, start_date: datetime = None, end_date: datetime = None
) -> list:
    """
    Get transaction history for a user (implementation in adapter)

    Args:
        user_id: User to get history for
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        list: Transaction records

    Raises:
        RuntimeError: If system not initialized
    """
    if _engine.db is None:
        raise RuntimeError("Payment system not initialized. Call initialize() first.")

    return _engine.db.get_transaction_history(user_id, start_date, end_date)

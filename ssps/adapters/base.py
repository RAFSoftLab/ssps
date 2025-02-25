from abc import ABC, abstractmethod
from datetime import datetime
from typing import ContextManager


class BaseDatabaseAdapter(ABC):
    """
    Base abstract class that carries methods to be implemented by database adapter.
    """

    class TransactionContext(ContextManager):
        @abstractmethod
        def __enter__(self):
            pass

        @abstractmethod
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    @abstractmethod
    def get_balance(self, user_id: str) -> float:
        """Get current balance for a user"""
        raise NotImplementedError

    @abstractmethod
    def update_balance(self, user_id: str, delta: float) -> None:
        """Update user balance. Use within atomic block."""
        raise NotImplementedError

    @abstractmethod
    def create_transaction_record(
        self,
        sender_id: str,
        recipient_id: str,
        amount: float,
        timestamp: datetime,
    ) -> None:
        """Store transaction record"""
        raise NotImplementedError

    @abstractmethod
    def transaction_context(self) -> TransactionContext:
        """Create atomic transaction context"""
        raise NotImplementedError

    @abstractmethod
    def get_transaction_history(
        self, user_id: str, start_date: datetime, end_date: datetime
    ):
        """Get transaction history for a user"""
        pass

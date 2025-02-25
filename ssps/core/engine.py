from datetime import datetime, timezone
from typing import Union

from ssps.adapters.base import BaseDatabaseAdapter
from ssps.core.exceptions import (
    InsufficientFundsError,
    SameRecipientError,
    NegativeAmountError,
)


class PaymentEngine:
    def __init__(self, db_adapter: BaseDatabaseAdapter):
        self.db = db_adapter

    def get_balance(self, sender_id: str) -> float:
        """Gets user balance. We can expose it here from the payment engine because
        it is common to use."""
        return self.db.get_balance(sender_id)

    def transfer(self, sender_id: str, recipient_id: str, amount: float) -> Union[bool]:
        """TODO: add docstring"""
        if amount <= 0:
            raise NegativeAmountError("Transfer amount must be positive")

        if sender_id == recipient_id:
            raise SameRecipientError("Cannot transfer to self")

        with self.db.transaction_context():
            # Check sender balance
            current_balance = self.get_balance(sender_id)
            if current_balance < amount:
                raise InsufficientFundsError(
                    f"Insufficient funds: {current_balance} available, {amount} required"
                )

            # Update balances
            self.db.update_balance(sender_id, -amount)
            self.db.update_balance(recipient_id, amount)

            # Record transaction
            timestamp = datetime.now(timezone.utc)
            self.db.create_transaction_record(
                sender_id, recipient_id, amount, timestamp
            )

        return True

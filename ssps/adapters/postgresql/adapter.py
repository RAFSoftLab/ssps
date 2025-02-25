import datetime
from contextlib import contextmanager
from typing import Dict, Any, List

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker

from ssps.adapters.postgresql.models import Base, Balance, Transaction
from ssps.adapters.base import BaseDatabaseAdapter


class PostgresAdapter(BaseDatabaseAdapter):
    def __init__(self, connection_string: str, user_model: type):
        """Initialize PostgreSQL adapter and create necessary tables if they don't already exist"""
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        self.user_model = user_model  # External user model
        Base.metadata.create_all(self.engine)

    def get_balance(self, user_id: str) -> float:
        with self.Session() as session:
            balance = session.query(Balance).get(user_id)
            return balance.amount if balance else 0.0

    def update_balance(self, user_id: str, delta: float) -> None:
        with self.Session() as session:
            balance = session.query(Balance).get(user_id)
            if balance:
                balance.amount += delta
            else:
                session.add(Balance(user_id=user_id, amount=delta))
            session.commit()

    def create_transaction_record(
        self,
        sender_id: str,
        recipient_id: str,
        amount: float,
        timestamp: datetime.datetime,
    ) -> None:
        with self.Session() as session:
            session.add(
                Transaction(
                    sender_id=sender_id,
                    recipient_id=recipient_id,
                    amount=amount,
                    timestamp=timestamp,
                )
            )
            session.commit()

    def get_transaction_history(
        self, user_id: str, start_date: datetime = None, end_date: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve transaction history for a user with optional date filtering

        Args:
            user_id: User to retrieve history for
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of transaction dictionaries with keys:
            - id: Unique transaction identifier (string)
            - direction: Transaction flow ("outgoing" or "incoming")
            - amount: Transaction amount in float
            - timestamp: ISO 8601 formatted transaction datetime
            - metadata: Additional transaction details containing:
                - original_sender: Original sender user ID
                - original_recipient: Original recipient user ID
                - reference_id: Original transaction ID reference
        """
        with self.Session() as session:
            # Base query
            query = session.query(Transaction).filter(
                or_(
                    Transaction.sender_id == user_id,
                    Transaction.recipient_id == user_id,
                )
            )

            # Apply date filters
            if start_date:
                query = query.filter(Transaction.timestamp >= start_date)  # noqa
            if end_date:
                query = query.filter(Transaction.timestamp <= end_date)  # noqa

            # Run query and format results
            transactions = query.order_by(Transaction.timestamp.desc()).all()

            return [
                self._format_transaction(txn, user_id) for txn in transactions  # noqa
            ]

    def _format_transaction(
        self, transaction: Transaction, user_id: str
    ) -> Dict[str, Any]:
        """Convert SQLAlchemy Transaction instance to dict"""
        is_outgoing = transaction.sender_id == user_id

        return {
            "id": str(transaction.id),
            "direction": "outgoing" if is_outgoing else "incoming",
            "amount": float(transaction.amount),
            "timestamp": transaction.timestamp.isoformat(),
            "metadata": {
                "original_sender": transaction.sender_id,
                "original_recipient": transaction.recipient_id,
                "reference_id": str(transaction.id),
            },
        }

    @contextmanager
    def transaction_context(self):
        """Provide atomic transaction context"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

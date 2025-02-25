from sqlalchemy import Column, String, Float, DateTime, UUID, text, Numeric
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class Balance(Base):
    __tablename__ = "balances"
    user_id = Column(String, primary_key=True)
    amount = Column(Float, default=0.0)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    sender_id = Column(String, nullable=False)
    recipient_id = Column(String, nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<Transaction {self.id} {self.sender_id}->{self.recipient_id} {self.amount}>"

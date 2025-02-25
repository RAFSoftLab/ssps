import pytest
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager

import ssps.api as api
from ssps.core import exceptions
from ssps.adapters.base import BaseDatabaseAdapter


class MockAdapter(BaseDatabaseAdapter):
    def __init__(self):
        self.users = {}
        self.balances = {}
        self.transactions = []
        self.committed = False

    def get_balance(self, user_id, session=None):
        return self.balances.get(user_id, 0.0)

    def update_balance(self, user_id, delta, session=None):
        self.balances[user_id] = self.balances.get(user_id, 0.0) + delta

    def create_transaction_record(
        self, sender_id, recipient_id, amount, timestamp, session=None
    ):
        self.transactions.append(
            {
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "amount": amount,
                "timestamp": timestamp,
            }
        )

    @contextmanager
    def transaction_context(self):
        try:
            yield self
            self.committed = True
        except:
            self.committed = False
            raise

    def get_transaction_history(self, user_id, start_date=None, end_date=None):
        return [
            txn
            for txn in self.transactions
            if (txn["sender_id"] == user_id or txn["recipient_id"] == user_id)
            and (not start_date or txn["timestamp"] >= start_date)
            and (not end_date or txn["timestamp"] <= end_date)
        ]


@pytest.fixture
def adapter():
    return MockAdapter()


@pytest.fixture(autouse=True)
def setup_teardown(adapter):
    # Setup
    adapter.users.update(
        {"user1": "USD", "user2": "USD", "user3": "EUR"}
    )  # TODO: remove currency
    adapter.balances.update({"user1": 1000.0, "user2": 500.0})
    api.initialize(adapter)
    yield
    # Teardown
    api.initialize(None)


class TestTransfer:
    def test_successful_transfer(self, adapter):
        api.transfer("user1", "user2", 100.0)
        assert adapter.balances["user1"] == 900.0
        assert adapter.balances["user2"] == 600.0
        assert len(adapter.transactions) == 1
        txn = adapter.transactions[0]
        assert txn["sender_id"] == "user1"
        assert txn["recipient_id"] == "user2"
        assert txn["amount"] == 100.0

    def test_insufficient_funds(self):
        with pytest.raises(exceptions.PaymentError) as exc:
            api.transfer("user1", "user2", 1500.0)
        assert "Insufficient funds" in str(exc.value)
        assert api.check_balance("user1") == 1000.0

    def test_same_sender_recipient(self):
        with pytest.raises(Exception) as exc:
            api.transfer("user1", "user1", 100.0)
        assert "Cannot transfer to self" in str(exc.value)

    def test_negative_amount(self):
        with pytest.raises(Exception) as exc:
            api.transfer("user1", "user2", -50.0)
        assert "positive" in str(exc.value).lower()


class TestCheckBalance:
    def test_existing_user(self):
        assert api.check_balance("user1") == 1000.0
        assert api.check_balance("user2") == 500.0

    def test_new_user(self):
        assert api.check_balance("new_user") == 0.0


class TestTransactionHistory:
    def test_history_retrieval(self, adapter):
        api.transfer("user1", "user2", 100.0)

        history = api.get_transaction_history("user1")
        assert len(history) == 1
        assert history[0]["amount"] == 100.0

        history = api.get_transaction_history("user2")
        assert len(history) == 1

    def test_date_filtering(self, adapter):
        old_date = datetime.now(timezone.utc) - timedelta(days=7)
        recent_date = datetime.now(timezone.utc)

        # Add old transaction
        adapter.transactions.append(
            {
                "sender_id": "user1",
                "recipient_id": "user2",
                "amount": 200.0,
                "timestamp": old_date,
            }
        )

        # Add recent transaction
        api.transfer("user1", "user2", 100.0)

        # Test filtering
        history = api.get_transaction_history(
            "user1", start_date=recent_date - timedelta(hours=1)
        )
        assert len(history) == 1
        assert history[0]["amount"] == 100.0


class TestInitialization:
    def test_uninitialized_api(self):
        api.initialize(None)
        with pytest.raises(RuntimeError) as exc:
            print(api._engine)
            api.transfer("user1", "user2", 100.0)
        assert "not initialized" in str(exc.value).lower()

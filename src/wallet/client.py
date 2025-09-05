# src/wallet/client.py
from typing import Tuple, Dict

class InMemoryWallet:
    """Very simple in-memory wallet used for dev/tests."""
    def __init__(self) -> None:
        self._bal: Dict[str, float] = {}

    def balance(self, user_id: str) -> float:
        return float(self._bal.get(user_id, 0.0))

    def credit(self, user_id: str, amount: float) -> float:
        amt = float(amount)
        self._bal[user_id] = self.balance(user_id) + amt
        return self._bal[user_id]

    def debit(self, user_id: str, amount: float) -> Tuple[bool, float]:
        amt = float(amount)
        cur = self.balance(user_id)
        new_bal = cur - amt
        if new_bal < 0:
            # not enough funds
            return False, cur
        self._bal[user_id] = new_bal
        return True, new_bal

# single shared test/dev wallet
_GLOBAL_WALLET = InMemoryWallet()

def get_wallet() -> InMemoryWallet:
    """Factory used by routers/services."""
    return _GLOBAL_WALLET

__all__ = ["InMemoryWallet", "get_wallet"]

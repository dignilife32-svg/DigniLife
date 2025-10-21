# src/wallet/client.py
# InMemory wallet client — dev/test helper only (NOT used in prod DB path)

from typing import Dict, Tuple


class InMemoryWallet:
    """Simple in‑memory wallet for local tests."""
    def __init__(self) -> None:
        self._bal: Dict[str, float] = {}

    def balance(self, user_id: str) -> float:
        return float(self._bal.get(user_id, 0.0))

    def credit(self, user_id: str, amount: float) -> float:
        new_bal = self._bal.get(user_id, 0.0) + float(amount)
        self._bal[user_id] = new_bal
        return new_bal

    def debit(self, user_id: str, amount: float) -> Tuple[bool, float]:
        cur = self._bal.get(user_id, 0.0)
        new_bal = cur - float(amount)
        if new_bal < 0:
            return False, cur
        self._bal[user_id] = new_bal
        return True, new_bal


# single global instance for tests
GLOBAL_WALLET = InMemoryWallet()


def get_wallet() -> InMemoryWallet:
    return GLOBAL_WALLET

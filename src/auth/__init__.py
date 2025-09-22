

# src/auth/__init__.py
from dataclasses import dataclass
from fastapi import Depends

@dataclass
class _User:
    id: str

def get_current_user(token: str | None = None) -> _User:
    # TODO: replace with real auth; for now always user "u_demo"
    return _User(id="u_demo")

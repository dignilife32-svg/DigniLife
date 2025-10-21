# src/routers/__init__.py
from importlib import import_module
from pathlib import Path
from fastapi import APIRouter

def iter_routers():
    """
    src/routers/*.py ထဲက file တိုင်းကို scan လုပ်ပြီး
    module ထဲမှာ `router` (APIRouter) ဆိုတဲ့ attribute ရှိရင် yield.
    """
    pkg_name = __name__              # "src.routers"
    pkg_dir = Path(__file__).parent  # .../src/routers

    for p in pkg_dir.glob("*.py"):
        if p.name.startswith("_"):
            continue                 # __init__.py / private မပါ
        mod = import_module(f"{pkg_name}.{p.stem}")
        router = getattr(mod, "router", None)
        if isinstance(router, APIRouter):
            yield router

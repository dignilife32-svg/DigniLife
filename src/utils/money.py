# src/utils/money.py
from decimal import Decimal, ROUND_HALF_UP, getcontext

# keep enough precision then quantize to 4 or 2 decimals per currency
getcontext().prec = 28

TWO_PLACES = Decimal("0.01")
FOUR_PLACES = Decimal("0.0001")

def as_money(x) -> Decimal:
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))

def q2(x: Decimal) -> Decimal:
    return x.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

def q4(x: Decimal) -> Decimal:
    return x.quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)

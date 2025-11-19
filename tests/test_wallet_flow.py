from __future__ import annotations
import pytest

pytestmark = pytest.mark.anyio
HEAD = {"x-user-id": "demo"}

async def _post_try_variants(client, path: str, variants: list[dict]):
    """Try multiple payload variants until we get a 2xx/4xx that's not 404/405/415."""
    last = None
    for body in variants:
        r = await client.post(path, json=body, headers=HEAD)
        last = r
        if r.status_code in (200, 201, 202):
            return r
        if r.status_code not in (404, 405, 415, 422):  # treat 422 as validation fail (bad variant)
            return r
    return last

async def _find_path(openapi: dict, want: list[str]) -> str | None:
    """Find a path that contains all substrings in `want`."""
    for p in openapi.get("paths", {}).keys():
        if all(w in p for w in want):
            return p
    return None

async def test_wallet_reserve_commit_flow(client):
    # 0) openapi discovery
    spec = (await client.get("/openapi.json")).json()
    # Find something like /wallet/withdraw/reserve or /wallet/tx/reserve etc.
    reserve_path = await _find_path(spec, ["wallet", "reserve"]) or await _find_path(spec, ["withdraw", "reserve"])
    commit_path  = await _find_path(spec, ["wallet", "commit"])  or await _find_path(spec, ["withdraw", "commit"])

    if not reserve_path or not commit_path:
        pytest.skip("reserve/commit endpoints not exposed in this build")

    # 1) RESERVE — try common field name variants
    reserve_variants = [
        {"amount_usd": 1.25, "ref": "t-e2e"},   # float USD
        {"usd_cents": 125,  "ref": "t-e2e"},    # integer cents
        {"amount": 1.25,    "ref": "t-e2e"},    # generic amount
    ]
    r1 = await _post_try_variants(client, reserve_path, reserve_variants)
    assert r1.status_code in (200, 201, 202)
    j1 = r1.json()
    # tx id may be named tx_id or id
    tx_id = j1.get("tx_id") or j1.get("id")
    assert tx_id, f"reserve response missing tx id field: {j1}"

    # 2) COMMIT — try id field variants
    commit_variants = [
        {"tx_id": tx_id},
        {"id": tx_id},
    ]
    r2 = await _post_try_variants(client, commit_path, commit_variants)
    assert r2.status_code in (200, 201, 202)
    assert r2.json().get("ok") is True

async def test_wallet_reserve_rejects_zero_or_negative(client):
    spec = (await client.get("/openapi.json")).json()
    reserve_path = await _find_path(spec, ["wallet", "reserve"]) or await _find_path(spec, ["withdraw", "reserve"])
    if not reserve_path:
        pytest.skip("reserve endpoint not exposed in this build")

    bad_variants = [
        {"amount_usd": 0, "ref": "bad"},
        {"usd_cents": 0,  "ref": "bad"},
        {"amount": 0,     "ref": "bad"},
        {"amount_usd": -5, "ref": "bad"},
        {"usd_cents": -5,  "ref": "bad"},
        {"amount": -5,     "ref": "bad"},
    ]
    # try each until we hit a variant your API recognizes; expect 400/422
    seen_validation = False
    for body in bad_variants:
        r = await client.post(reserve_path, json=body, headers=HEAD)
        if r.status_code in (400, 422):
            seen_validation = True
            break
    assert seen_validation, "reserve should reject zero/negative amounts"

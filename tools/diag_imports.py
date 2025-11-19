# tools/diag_imports.py
from __future__ import annotations
import os, sys, traceback, importlib, inspect, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(ROOT))  # allow "src.*" imports

def as_module(path: Path) -> str | None:
    if path.name.startswith("_"): return None
    if path.suffix != ".py": return None
    rel = path.relative_to(ROOT).with_suffix("")
    parts = list(rel.parts)
    # expect path like src/foo/bar.py  ->  src.foo.bar
    return ".".join(parts)

def scan():
    results = {"ok": [], "fail": []}
    for py in SRC.rglob("*.py"):
        mod = as_module(py)
        if not mod: 
            continue
        try:
            m = importlib.import_module(mod)
            # Router introspection
            routers = []
            try:
                from fastapi import APIRouter  # type: ignore
                for name, obj in vars(m).items():
                    if isinstance(obj, APIRouter):
                        # collect route infos
                        routes = []
                        for r in obj.routes:
                            try:
                                routes.append({"path": getattr(r, "path", "?"), "methods": list(getattr(r, "methods", []))})
                            except Exception:
                                pass
                        routers.append({"var": name, "routes": routes})
            except Exception:
                pass
            results["ok"].append({"module": mod, "routers": routers})
        except Exception as e:
            tb = traceback.format_exc(limit=2)
            etype = type(e).__name__
            results["fail"].append({"module": mod, "etype": etype, "msg": str(e), "where": tb})
    return results

if __name__ == "__main__":
    res = scan()
    print("=== IMPORT OK ===")
    for it in res["ok"]:
        r = it["routers"]
        if r:
            print(f"OK {it['module']}  -> routers: " + ", ".join(f"{ri['var']}[{len(ri['routes'])}]" for ri in r))
        else:
            print(f"OK {it['module']}")
    print("\n=== IMPORT FAIL ===")
    for it in res["fail"]:
        print(f"FAIL {it['module']} -> {it['etype']}: {it['msg']}")
        print(it["where"].rstrip())
    # quick summary
    print("\nSUMMARY:", json.dumps({k: len(v) for k,v in res.items()}))

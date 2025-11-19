# src/ai/face.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Protocol, Optional
import base64, hashlib, math

# ========= Provider Protocol =========
class FaceProvider(Protocol):
    async def embed_from_b64(self, img_b64: str) -> List[float]: ...
    def match(self, vec1: List[float], vec2: List[float]) -> Tuple[bool, float]: ...
    def liveness_score(self, img_b64: str) -> float: ...

# ========= Utils =========
def _b64_to_bytes(s: str) -> bytes:
    try:
        return base64.b64decode(s, validate=True)
    except Exception as e:
        raise ValueError("INVALID_BASE64") from e

def _normalize(v: List[float]) -> List[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]

def _cosine(a: List[float], b: List[float]) -> float:
    n = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(n))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return max(0.0, min(1.0, dot / (na * nb)))

# ========= DEV Mock Provider (deterministic; for local/dev) =========
class DevMockProvider:
    dim: int = 128
    match_threshold: float = 0.87

    async def embed_from_b64(self, img_b64: str) -> List[float]:
        raw = _b64_to_bytes(img_b64)
        h = hashlib.sha256(raw).digest()
        vec = [b / 255.0 for b in h]
        while len(vec) < self.dim:
            h = hashlib.sha256(h).digest()
            vec.extend(b / 255.0 for b in h)
        return _normalize(vec[: self.dim])

    def match(self, vec1: List[float], vec2: List[float]) -> Tuple[bool, float]:
        sim = _cosine(vec1, vec2)
        return (sim >= self.match_threshold, float(sim))

    def liveness_score(self, img_b64: str) -> float:
        # very simple entropy proxy (0..1), OK for dev only
        raw = _b64_to_bytes(img_b64)
        buckets = [0] * 16
        for b in raw[:4096]:
            buckets[b % 16] += 1
        total = sum(buckets) or 1
        probs = [c / total for c in buckets]
        ent = -sum(p * math.log(p + 1e-9) for p in probs)      # ~0..2.8
        return max(0.0, min(1.0, ent / 2.8))

# ========= External Provider skeleton (wire real SDK later) =========
@dataclass
class ExternalFaceProvider:
    name: str = "external"
    match_threshold: float = 0.90

    async def embed_from_b64(self, img_b64: str) -> List[float]:
        raise NotImplementedError("Plug in real embedding SDK")

    def match(self, vec1: List[float], vec2: List[float]) -> Tuple[bool, float]:
        sim = _cosine(vec1, vec2)  # placeholder until SDK returns score
        return (sim >= self.match_threshold, float(sim))

    def liveness_score(self, img_b64: str) -> float:
        raise NotImplementedError("Plug in real liveness SDK")

# ========= Provider selection (can be swapped later) =========
_PROVIDER: FaceProvider = DevMockProvider()

def get_provider() -> FaceProvider:
    """Backward-compatible getter used by some modules/tests."""
    return _PROVIDER

# ========= Module-level API (backward-compatible names) =========
async def face_embed(image_b64: str) -> List[float]:
    return await _PROVIDER.embed_from_b64(image_b64)

def face_match(vec1: List[float], vec2: List[float], thresh: Optional[float] = None) -> bool:
    ok, score = _PROVIDER.match(vec1, vec2)
    return (score >= float(thresh)) if thresh is not None else ok

def face_liveness(image_b64: str) -> float:
    return _PROVIDER.liveness_score(image_b64)

# aliases for old imports
liveness_score = face_liveness  # some code imports this exact name

__all__ = [
    "face_embed",
    "face_match",
    "face_liveness",
    "liveness_score",       # alias
    "get_provider",         # for tests/advanced usage
    "FaceProvider",
    "DevMockProvider",
    "ExternalFaceProvider",
]

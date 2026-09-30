"""Deterministic randomness.

Python's built-in hash() is process-randomized, so all seeds go through
SHA-256 first. The same session seed must reproduce the same plan forever.
"""
from __future__ import annotations

import hashlib
import random


def stable_seed(*parts: object) -> int:
    material = ":".join(str(p) for p in parts)
    return int.from_bytes(hashlib.sha256(material.encode("utf-8")).digest()[:8], "big")


def make_rng(*parts: object) -> random.Random:
    return random.Random(stable_seed(*parts))

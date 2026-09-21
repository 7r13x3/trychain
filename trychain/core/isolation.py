"""
TryChain — Circuit Isolation
Every connection gets its own unique route through the proxy pool.
"""
import hashlib
import random


def isolate_chain(proxies, session_key: str, min_hops: int = 2):
    """
    Return a shuffled subset of `proxies` for this specific session.

    session_key is typically "client_ip:target_host:target_port".
    Same key -> same route (so the same flow stays coherent).
    Different key -> different route.
    """
    if not proxies:
        return []

    # deterministic shuffle based on session_key
    seed_bytes = hashlib.sha256(session_key.encode()).digest()
    seed = int.from_bytes(seed_bytes, "big")
    rng = random.Random(seed)

    shuffled = list(proxies)
    rng.shuffle(shuffled)

    # pick a random number of hops between min_hops and len(proxies)
    upper = len(shuffled)
    lower = min(min_hops, upper)
    n = rng.randint(lower, upper)
    return shuffled[:n]

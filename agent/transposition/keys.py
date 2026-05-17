import numpy as np

_rng = np.random.default_rng(seed=12345678)

TABLE: np.ndarray = _rng.integers(
    low=0, high=np.iinfo(np.int64).max, size=(64, 2, 16), dtype=np.int64
)

# XOR this in whenever it is BLUE's turn to move.
SIDE_KEY: int = int(_rng.integers(0, np.iinfo(np.int64).max, dtype=np.int64))

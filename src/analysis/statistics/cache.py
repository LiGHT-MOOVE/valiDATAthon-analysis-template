from pathlib import Path

from joblib import Memory


def get_cache(cache_dir: Path, enabled: bool = True) -> Memory:
    """Create a Joblib cache using the configured directory."""

    return Memory(
        location=cache_dir if enabled else None,
        verbose=0,
    )

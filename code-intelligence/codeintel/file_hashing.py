import hashlib
from pathlib import Path

def generate_file_id(repository_key: str, relative_path: str) -> str:
    """Generates a stable file_id from repository_key and relative_path."""
    # Normalize slashes to make IDs consistent across OS platforms
    normalized_path = relative_path.replace('\\', '/')
    key_str = f"{repository_key}:{normalized_path}"
    return hashlib.sha256(key_str.encode('utf-8')).hexdigest()

def compute_file_hash(file_path: Path) -> str:
    """Computes SHA-256 hash of a file's content in chunks."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in 64kb chunks
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        # If file doesn't exist or can't be read, return empty string or raise
        # For indexing, raising is better so we don't index corrupted files
        raise IOError(f"Could not read file {file_path} to compute hash: {e}")

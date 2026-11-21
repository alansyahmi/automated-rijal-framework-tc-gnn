"""Portable SHA-256 and manifest path helpers.

Text files checked out across Windows (CRLF) and POSIX (LF) platforms must
produce identical digests when normalized with ``\\r\\n -> \\n``.
"""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
from typing import Union

PathLike = Union[str, Path]


def sha256_bytes_normalized(data: bytes) -> str:
    """Return the SHA-256 hex digest after normalizing CRLF to LF."""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def sha256_text_normalized(path: PathLike) -> str:
    """Return the LF-normalized SHA-256 hex digest of ``path``."""
    return sha256_bytes_normalized(Path(path).read_bytes())


def sha256_file(path: PathLike) -> str:
    """Return the raw-byte SHA-256 hex digest of ``path``."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_manifest_path(path_str: Union[str, Path]) -> Path:
    """Convert a manifest path (POSIX or Windows) into a local ``Path``."""
    return Path(str(path_str).replace("\\", "/"))


def to_posix_relative(path: Path, root: Path) -> str:
    """Return a POSIX relative path string from ``root`` to ``path``."""
    return PurePosixPath(path.resolve().relative_to(root.resolve()).as_posix()).as_posix()

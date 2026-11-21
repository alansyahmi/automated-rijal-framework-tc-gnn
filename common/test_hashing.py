"""Unit tests for portable hashing and manifest path helpers."""

from __future__ import annotations

from pathlib import Path

from common.hashing import (
    normalize_manifest_path,
    sha256_bytes_normalized,
    sha256_file,
    sha256_text_normalized,
)


def test_sha256_text_normalized_matches_across_crlf_and_lf(tmp_path: Path) -> None:
    lf_path = tmp_path / "sample_lf.csv"
    crlf_path = tmp_path / "sample_crlf.csv"
    lf_bytes = "id,text\n1,ثقة\n2,صدوق\n".encode("utf-8")
    crlf_bytes = lf_bytes.replace(b"\n", b"\r\n")
    lf_path.write_bytes(lf_bytes)
    crlf_path.write_bytes(crlf_bytes)

    assert sha256_file(lf_path) != sha256_file(crlf_path)
    assert sha256_text_normalized(lf_path) == sha256_text_normalized(crlf_path)
    assert sha256_bytes_normalized(crlf_bytes) == sha256_text_normalized(lf_path)


def test_normalize_manifest_path_accepts_windows_and_posix() -> None:
    win = r"data\1_raw\Shamela4_Full_DB\_meta\narrators.parquet"
    posix = "data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet"
    assert normalize_manifest_path(win) == Path(posix)
    assert normalize_manifest_path(posix) == Path(posix)

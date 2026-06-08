"""Staged-path secret name scan plus a narrow high-confidence content scan.

The path scan blocks secret-like file names (`.env`, `*.pem`, credential/token
paths). The content scan adds a second line of defense for *committed secret
material* using only unambiguous markers (private-key PEM headers, AWS access-key
IDs, Slack bot tokens, GitHub PATs) that effectively never appear in legitimate
source. Patterns are intentionally narrow to avoid false-positives on the live
autonomous run; the whole tree was verified clean before this was added.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path, PurePosixPath


FORBIDDEN_SUFFIXES = {".key", ".pem"}

# High-confidence secret-content markers. Keep these unambiguous on purpose.
SECRET_CONTENT_RE = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"
    r"|AKIA[0-9A-Z]{16}"
    r"|xoxb-[0-9A-Za-z-]{10,}"
    r"|ghp_[0-9A-Za-z]{36}"
)
# Only scan plausibly-text source/config/data files; skip binaries and huge files.
CONTENT_SCAN_MAX_BYTES = 2_000_000
CONTENT_SCAN_SKIP_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".zst", ".parquet",
    ".sqlite", ".db", ".onnx", ".pkl", ".pt", ".pth", ".feather", ".arrow", ".dbn",
}


def is_security_tooling_path(path: str) -> bool:
    """True for the secret/canary/guard tooling and its tests/fixtures, which
    legitimately embed secret-pattern strings as fixtures. Mirrors the path-scan's
    SECRET_TOOLING_TOKENS exemption so the content scan does not flag itself."""
    tokens: list[str] = []
    for part in path_parts(path):
        tokens.extend(name_tokens(part))
    return bool(SECRET_TOOLING_TOKENS.intersection(tokens))


def has_secret_content(path: str) -> bool:
    """Return True if a readable text file contains a high-confidence secret marker.

    Fails closed only on a positive match; any read/size/binary issue returns
    False so the scan never blocks on unreadable input. Security-tooling and its
    fixtures are exempt (they embed the patterns on purpose).
    """
    if is_security_tooling_path(path):
        return False
    try:
        p = Path(path)
        if not p.is_file():
            return False
        if p.suffix.lower() in CONTENT_SCAN_SKIP_SUFFIXES:
            return False
        if p.stat().st_size > CONTENT_SCAN_MAX_BYTES:
            return False
        text = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return SECRET_CONTENT_RE.search(text) is not None
SECRET_TOKENS = {"secret", "secrets"}
SECRET_TOOLING_TOKENS = {"canary", "forbidden", "guard", "policy", "scan", "scanner", "scanning"}
TOKEN_TOKENS = {"token", "tokens"}
CREDENTIAL_TOKENS = {"credential", "credentials"}
TOKEN_RE = re.compile(r"[a-z0-9]+")


def path_parts(path: str) -> list[str]:
    return [part for part in path.replace("\\", "/").split("/") if part and part != "."]


def effective_name(name: str) -> str:
    lowered = name.lower()
    return lowered[:-3] if lowered.endswith(".j2") else lowered


def name_tokens(name: str) -> list[str]:
    return TOKEN_RE.findall(effective_name(name))


def has_private_key_tokens(tokens: list[str]) -> bool:
    return any(left == "private" and right == "key" for left, right in zip(tokens, tokens[1:]))


def has_secret_artifact_tokens(tokens: list[str]) -> bool:
    if not SECRET_TOKENS.intersection(tokens):
        return False
    return not SECRET_TOOLING_TOKENS.intersection(tokens)


def is_forbidden_part(part: str) -> bool:
    name = effective_name(part)
    if name == ".env" or name.startswith(".env."):
        return True
    if PurePosixPath(name).suffix.lower() in FORBIDDEN_SUFFIXES:
        return True

    tokens = name_tokens(part)
    return (
        bool(CREDENTIAL_TOKENS.intersection(tokens))
        or bool(TOKEN_TOKENS.intersection(tokens))
        or has_private_key_tokens(tokens)
        or has_secret_artifact_tokens(tokens)
    )


def is_forbidden(path: str) -> bool:
    return any(is_forbidden_part(part) for part in path_parts(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Block secret-like paths and committed secret material.")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    violations: list[str] = []
    for path in args.paths:
        if is_forbidden(path):
            print(f"Secret-like path is not allowed: {path}")
            violations.append(path)
        elif has_secret_content(path):
            print(f"High-confidence secret material detected in: {path}")
            violations.append(path)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())

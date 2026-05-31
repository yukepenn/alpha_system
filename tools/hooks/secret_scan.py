"""Simple staged-path secret name scan."""

from __future__ import annotations

import argparse
import re
from pathlib import PurePosixPath


FORBIDDEN_SUFFIXES = {".key", ".pem"}
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
    parser = argparse.ArgumentParser(description="Block obvious secret-like paths.")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    violations = [path for path in args.paths if is_forbidden(path)]
    for violation in violations:
        print(f"Secret-like path is not allowed: {violation}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())

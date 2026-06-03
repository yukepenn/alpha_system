from __future__ import annotations

from tools import verify


def test_check_required_files_returns_zero_at_repo_root() -> None:
    assert verify.check_required_files() == 0


def test_argparse_exposes_expected_flags() -> None:
    parser = verify.build_parser()
    option_strings = {
        option_string for action in parser._actions for option_string in action.option_strings
    }

    assert {
        "--smoke",
        "--lint",
        "--typecheck",
        "--test",
        "--all",
        "--ci",
        "--boundaries",
        "--artifacts",
    } <= option_strings


def test_run_typecheck_returns_zero() -> None:
    assert verify.run_typecheck() == 0


def test_check_git_environment_custom_index_and_opt_in(monkeypatch) -> None:
    monkeypatch.delenv("ALPHA_SYSTEM_ALLOW_CUSTOM_GIT_ENV", raising=False)
    monkeypatch.setenv("GIT_INDEX_FILE", "/tmp/alpha-system-test-index")

    assert verify.check_git_environment() == 1

    monkeypatch.delenv("GIT_INDEX_FILE", raising=False)

    assert verify.check_git_environment() == 0

    monkeypatch.setenv("GIT_INDEX_FILE", "/tmp/alpha-system-test-index")
    monkeypatch.setenv("ALPHA_SYSTEM_ALLOW_CUSTOM_GIT_ENV", "1")

    assert verify.check_git_environment() == 0

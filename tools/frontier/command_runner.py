"""Safe subprocess runner for Frontier runtime tools.

The runner is intentionally small: no shell execution, bounded timeouts,
captured output, and optional artifact files for later review.
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import threading
import time
from contextlib import suppress
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TIMEOUT_SECONDS = 600
TIMEOUT_RETURN_CODE = 124
MAX_DISPLAY_ARG_CHARS = 240
MAX_DISPLAY_COMMAND_CHARS = 4000

DESTRUCTIVE_COMMAND_PREFIXES: tuple[tuple[str, ...], ...] = (
    ("git", "reset", "--hard"),
    ("git", "clean", "-fd"),
    ("git", "clean", "-fdx"),
    ("git", "push", "--force"),
    ("git", "push", "-f"),
    ("rm", "-rf"),
    ("rm", "-fr"),
)


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    return_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False
    cwd: str | None = None
    stdin_source: str | None = None
    stdin_path: str | None = None
    stdin_digest: str | None = None
    stdin_bytes: int | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None
    result_path: str | None = None

    @property
    def returncode(self) -> int:
        """Compatibility alias for subprocess.CompletedProcess-style callers."""

        return self.return_code

    @property
    def ok(self) -> bool:
        return self.return_code == 0 and not self.timed_out


@dataclass(frozen=True)
class ProviderWatchdogConfig:
    """Progress watchdog for long provider subprocesses.

    Defaults implement the phase contract: sample about every 30s; kill only
    after wall-clock exceeds 60s, the process-group CPU tick delta is exactly
    zero (`cpu_tick_epsilon=0`), and the run events file has not grown.
    """

    events_path: Path | None
    event_writer: Callable[[str, Mapping[str, Any]], None] | None = None
    sample_interval_seconds: float = 30.0
    hang_after_seconds: float = 60.0
    cpu_tick_epsilon: int = 0
    kill_grace_seconds: float = 5.0
    event_name: str = "PROVIDER_HANG_DETECTED"


@dataclass(frozen=True)
class _EventSnapshot:
    size: int
    mtime_ns: int


def _normalize_command(command: Sequence[str]) -> list[str]:
    if isinstance(command, (str, bytes)):
        raise TypeError("CommandRunner requires a sequence of arguments, not a shell string.")
    normalized = [str(part) for part in command]
    if not normalized:
        raise ValueError("CommandRunner requires a non-empty command.")
    return normalized


def _matches_prefix(command: Sequence[str], prefix: Sequence[str]) -> bool:
    return len(command) >= len(prefix) and tuple(command[: len(prefix)]) == tuple(prefix)


def assert_safe_command(command: Sequence[str]) -> None:
    normalized = _normalize_command(command)
    for prefix in DESTRUCTIVE_COMMAND_PREFIXES:
        if _matches_prefix(normalized, prefix):
            raise ValueError(f"Refusing destructive command: {' '.join(normalized)}")
    if len(normalized) >= 3 and normalized[:2] == ["git", "add"] and normalized[2] in {".", "-A"}:
        raise ValueError(f"Refusing broad git staging command: {' '.join(normalized)}")


def _safe_artifact_stem(value: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip(".-")
    return stem[:80] or "command"


def _digest_text(value: str) -> tuple[str, int]:
    data = value.encode("utf-8")
    return sha256(data).hexdigest(), len(data)


def _digest_file(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return sha256(data).hexdigest(), len(data)


def _redact_arg(value: str) -> str:
    if len(value) <= MAX_DISPLAY_ARG_CHARS:
        return value
    digest, byte_count = _digest_text(value)
    return f"<redacted:{byte_count} bytes sha256:{digest[:12]}>"


def _display_command(command: Sequence[str], display_command: Sequence[str] | None = None) -> list[str]:
    raw = _normalize_command(display_command or command)
    displayed = [_redact_arg(part) for part in raw]
    if sum(len(part) + 1 for part in displayed) <= MAX_DISPLAY_COMMAND_CHARS:
        return displayed
    digest, byte_count = _digest_text("\0".join(raw))
    head = displayed[:8]
    head.append(f"<redacted-command:{byte_count} bytes sha256:{digest[:12]}>")
    return head


def _proc_stat_ticks(pid: int) -> int | None:
    try:
        text = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except OSError:
        return None
    rparen = text.rfind(")")
    if rparen == -1:
        return None
    fields = text[rparen + 2 :].split()
    try:
        return int(fields[11]) + int(fields[12])
    except (IndexError, ValueError):
        return None


def _process_group_pids(pid: int) -> tuple[int, ...]:
    try:
        pgid = os.getpgid(pid)
    except OSError:
        return ()
    pids: list[int] = []
    proc_root = Path("/proc")
    try:
        entries = tuple(proc_root.iterdir())
    except OSError:
        return (pid,)
    for entry in entries:
        if not entry.name.isdigit():
            continue
        candidate = int(entry.name)
        try:
            if os.getpgid(candidate) == pgid:
                pids.append(candidate)
        except OSError:
            continue
    return tuple(sorted(set(pids))) or (pid,)


def _cpu_ticks_for_process_group(pid: int) -> int | None:
    ticks = 0
    seen = False
    for member_pid in _process_group_pids(pid):
        value = _proc_stat_ticks(member_pid)
        if value is None:
            continue
        ticks += value
        seen = True
    return ticks if seen else None


def _event_snapshot(path: Path | None) -> _EventSnapshot:
    if path is None:
        return _EventSnapshot(size=0, mtime_ns=0)
    try:
        stat = path.stat()
    except OSError:
        return _EventSnapshot(size=0, mtime_ns=0)
    return _EventSnapshot(size=stat.st_size, mtime_ns=stat.st_mtime_ns)


def _event_grew(previous: _EventSnapshot, current: _EventSnapshot) -> bool:
    return current.size > previous.size or current.mtime_ns > previous.mtime_ns


def _wchan(pid: int) -> str | None:
    try:
        return Path(f"/proc/{pid}/wchan").read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def _append_raw_watchdog_event(events_path: Path | None, event: str, details: Mapping[str, Any]) -> None:
    if events_path is None:
        return
    try:
        events_path.parent.mkdir(parents=True, exist_ok=True)
        with events_path.open("a", encoding="utf-8") as handle:
            payload = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": event, **details}
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
    except OSError:
        return


def _kill_process_group(process: subprocess.Popen[str], *, grace_seconds: float) -> None:
    if process.poll() is not None:
        return
    try:
        pgid = os.getpgid(process.pid)
    except OSError:
        process.kill()
        return
    with suppress(ProcessLookupError):
        os.killpg(pgid, signal.SIGTERM)
    try:
        process.wait(timeout=max(0.0, grace_seconds))
        return
    except subprocess.TimeoutExpired:
        with suppress(ProcessLookupError):
            os.killpg(pgid, signal.SIGKILL)
        with suppress(subprocess.TimeoutExpired):
            process.wait(timeout=max(0.0, grace_seconds))


class _ProviderWatchdog:
    def __init__(self, process: subprocess.Popen[str], config: ProviderWatchdogConfig) -> None:
        self.process = process
        self.config = config
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name=f"provider-watchdog-{process.pid}", daemon=True)
        self.triggered_details: dict[str, Any] | None = None

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1.0)

    def _emit(self, details: Mapping[str, Any]) -> None:
        if self.config.event_writer is not None:
            try:
                self.config.event_writer(self.config.event_name, details)
            except Exception:
                _append_raw_watchdog_event(self.config.events_path, self.config.event_name, details)
            return
        _append_raw_watchdog_event(self.config.events_path, self.config.event_name, details)

    def _run(self) -> None:
        started = time.monotonic()
        last_ticks = _cpu_ticks_for_process_group(self.process.pid)
        last_events = _event_snapshot(self.config.events_path)
        last_event_growth = started
        interval = max(0.01, float(self.config.sample_interval_seconds))
        while not self._stop.wait(interval):
            if self.process.poll() is not None:
                return
            now = time.monotonic()
            ticks = _cpu_ticks_for_process_group(self.process.pid)
            events = _event_snapshot(self.config.events_path)
            event_growth = _event_grew(last_events, events)
            if event_growth:
                last_event_growth = now
            cpu_delta: int | None = None
            if ticks is not None and last_ticks is not None:
                cpu_delta = ticks - last_ticks
            wall_seconds = now - started
            frozen_cpu = cpu_delta is not None and cpu_delta <= self.config.cpu_tick_epsilon
            if wall_seconds > self.config.hang_after_seconds and frozen_cpu and not event_growth:
                details = {
                    "pid": self.process.pid,
                    "pgid": _safe_getpgid(self.process.pid),
                    "wall_seconds": round(wall_seconds, 3),
                    "cpu_delta": cpu_delta,
                    "last_event_age_seconds": round(now - last_event_growth, 3),
                    "events_path": str(self.config.events_path) if self.config.events_path is not None else None,
                    "wchan": _wchan(self.process.pid),
                }
                self.triggered_details = details
                self._emit(details)
                _kill_process_group(self.process, grace_seconds=self.config.kill_grace_seconds)
                return
            last_ticks = ticks
            last_events = events


def _safe_getpgid(pid: int) -> int | None:
    try:
        return os.getpgid(pid)
    except OSError:
        return None


class CommandRunner:
    """Run commands with captured output and optional artifact persistence."""

    def __init__(self, root: Path | None = None, artifact_dir: Path | None = None) -> None:
        self.root = (root or ROOT).resolve()
        self.artifact_dir = artifact_dir

    def _resolve_cwd(self, cwd: Path | str | None) -> Path:
        if cwd is None:
            return self.root
        candidate = Path(cwd)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()

    def _artifact_paths(self, prefix: str) -> tuple[Path, Path, Path] | tuple[None, None, None]:
        if self.artifact_dir is None:
            return None, None, None
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        stem = _safe_artifact_stem(prefix)
        return (
            self.artifact_dir / f"{stem}.stdout.txt",
            self.artifact_dir / f"{stem}.stderr.txt",
            self.artifact_dir / f"{stem}.result.json",
        )

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path | str | None = None,
        env: Mapping[str, str] | None = None,
        timeout_seconds: int | float | None = None,
        artifact_prefix: str | None = None,
        stdin_text: str | None = None,
        stdin_path: Path | str | None = None,
        display_command: Sequence[str] | None = None,
        provider_watchdog: ProviderWatchdogConfig | None = None,
    ) -> CommandResult:
        if stdin_text is not None and stdin_path is not None:
            raise ValueError("Pass either stdin_text or stdin_path, not both.")
        normalized = _normalize_command(command)
        assert_safe_command(normalized)
        command_for_logs = _display_command(normalized, display_command)
        resolved_cwd = self._resolve_cwd(cwd)
        merged_env = os.environ.copy()
        if env:
            merged_env.update({str(key): str(value) for key, value in env.items()})

        started = time.monotonic()
        stdout = ""
        stderr = ""
        return_code = 0
        timed_out = False
        timeout = timeout_seconds if timeout_seconds is not None else DEFAULT_TIMEOUT_SECONDS
        stdin_source: str | None = None
        stdin_path_value: str | None = None
        stdin_digest: str | None = None
        stdin_bytes: int | None = None

        resolved_stdin_path: Path | None = None
        if stdin_text is not None:
            stdin_source = "stdin_text"
            stdin_digest, stdin_bytes = _digest_text(stdin_text)
        elif stdin_path is not None:
            candidate = Path(stdin_path)
            if not candidate.is_absolute():
                candidate = resolved_cwd / candidate
            resolved_stdin_path = candidate.resolve()
            stdin_source = "stdin_path"
            stdin_path_value = str(resolved_stdin_path)
            stdin_digest, stdin_bytes = _digest_file(resolved_stdin_path)

        try:
            stdin_file = None
            try:
                if resolved_stdin_path is not None:
                    stdin_file = resolved_stdin_path.open("r", encoding="utf-8")
                    stdin_stream = stdin_file
                    input_text = None
                elif stdin_text is not None:
                    stdin_stream = subprocess.PIPE
                    input_text = stdin_text
                else:
                    stdin_stream = None
                    input_text = None
                process = subprocess.Popen(
                    normalized,
                    cwd=resolved_cwd,
                    env=merged_env,
                    text=True,
                    stdin=stdin_stream,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=provider_watchdog is not None,
                )
                watchdog = _ProviderWatchdog(process, provider_watchdog) if provider_watchdog is not None else None
                if watchdog is not None:
                    watchdog.start()
                try:
                    stdout, stderr = process.communicate(input=input_text, timeout=timeout)
                    return_code = process.returncode
                except subprocess.TimeoutExpired as error:
                    stdout = error.stdout or ""
                    stderr = error.stderr or ""
                    if isinstance(stdout, bytes):
                        stdout = stdout.decode("utf-8", errors="replace")
                    if isinstance(stderr, bytes):
                        stderr = stderr.decode("utf-8", errors="replace")
                    if provider_watchdog is not None:
                        _kill_process_group(process, grace_seconds=provider_watchdog.kill_grace_seconds)
                    else:
                        process.kill()
                    extra_stdout, extra_stderr = process.communicate()
                    stdout += extra_stdout or ""
                    stderr += extra_stderr or ""
                    stderr = (stderr + "\n" if stderr else "") + f"Command timed out after {timeout} seconds."
                    return_code = TIMEOUT_RETURN_CODE
                    timed_out = True
                finally:
                    if watchdog is not None:
                        watchdog.stop()
                        if watchdog.triggered_details is not None:
                            return_code = TIMEOUT_RETURN_CODE
                            timed_out = True
                            wall = watchdog.triggered_details.get("wall_seconds")
                            stderr = (
                                (stderr + "\n" if stderr else "")
                                + f"Provider watchdog detected a hung provider process group after {wall} seconds."
                            )
            finally:
                if stdin_file is not None:
                    stdin_file.close()
        except subprocess.TimeoutExpired as error:
            stdout = error.stdout or ""
            stderr = error.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            stderr = (stderr + "\n" if stderr else "") + f"Command timed out after {timeout} seconds."
            return_code = TIMEOUT_RETURN_CODE
            timed_out = True
        except FileNotFoundError as error:
            stdout = ""
            stderr = str(error)
            return_code = 127
        except OSError as error:
            stdout = ""
            stderr = str(error)
            return_code = 126

        duration_ms = int((time.monotonic() - started) * 1000)
        result = CommandResult(
            command=command_for_logs,
            return_code=return_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            timed_out=timed_out,
            cwd=str(resolved_cwd),
            stdin_source=stdin_source,
            stdin_path=stdin_path_value,
            stdin_digest=stdin_digest,
            stdin_bytes=stdin_bytes,
        )

        if artifact_prefix:
            stdout_path, stderr_path, result_path = self._artifact_paths(artifact_prefix)
            if stdout_path and stderr_path and result_path:
                stdout_path.write_text(stdout, encoding="utf-8")
                stderr_path.write_text(stderr, encoding="utf-8")
                result_data = asdict(result)
                result_data["stdout_path"] = str(stdout_path)
                result_data["stderr_path"] = str(stderr_path)
                result_data["result_path"] = str(result_path)
                result_path.write_text(json.dumps(result_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                result = CommandResult(
                    **{
                        **asdict(result),
                        "stdout_path": str(stdout_path),
                        "stderr_path": str(stderr_path),
                        "result_path": str(result_path),
                    }
                )

        return result

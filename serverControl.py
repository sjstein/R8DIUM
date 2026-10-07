#########################
# R8DIUM : Run8 Database for Integrated User Management
##########################
"""Cross-platform Run8 server lifecycle controls.

Windows installations retain the original process-based behavior when no
commands are configured.  Linux and container installations should configure
explicit commands which talk to a narrowly scoped Run8 supervisor.
"""

from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import subprocess


RUN8_EXECUTABLE = 'Run-8 Train Simulator V3.exe'
CONTROL_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class ControlResult:
    success: bool
    message: str


def _command_arguments(command: str) -> list[str]:
    """Split a trusted configuration command without invoking a shell."""
    return shlex.split(command, posix=os.name != 'nt')


def _run_arguments(arguments: list[str], launch_path: str) -> ControlResult:
    try:
        completed = subprocess.run(
            arguments,
            cwd=launch_path or None,
            capture_output=True,
            text=True,
            timeout=CONTROL_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        return ControlResult(False, f'Lifecycle command failed: {error}')

    detail = (completed.stdout or completed.stderr).strip()
    if completed.returncode != 0:
        message = f'Lifecycle command exited with status {completed.returncode}.'
        if detail:
            message += f' {detail}'
        return ControlResult(False, message)

    return ControlResult(True, detail or 'Lifecycle command completed successfully.')


def _run_command(command: str, launch_path: str) -> ControlResult:
    if not command.strip():
        return ControlResult(False, 'No lifecycle command is configured.')
    return _run_arguments(_command_arguments(command), launch_path)


def _same_executable(executable: str | None, launch_path: str) -> bool:
    if not executable:
        return False
    expected = os.path.normcase(os.path.abspath(Path(launch_path) / RUN8_EXECUTABLE))
    actual = os.path.normcase(os.path.abspath(executable))
    return actual == expected


def _stop_windows_server(server_name: str, launch_path: str) -> ControlResult:
    if os.name != 'nt':
        return ControlResult(
            False,
            f'No stop_command is configured for Linux server {server_name}.',
        )

    import psutil

    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] == RUN8_EXECUTABLE and _same_executable(proc.info['exe'], launch_path):
                proc.terminate()
                return ControlResult(
                    True,
                    f'Server {server_name} (PID {proc.info["pid"]}) termination initiated.',
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return ControlResult(False, f'No running server matching {server_name} was found.')


def _start_windows_server(server_name: str, launch_path: str) -> ControlResult:
    if os.name != 'nt':
        return ControlResult(
            False,
            f'No start_command is configured for Linux server {server_name}.',
        )

    start_script = Path(launch_path) / 'startServer.bat'
    if not start_script.is_file():
        return ControlResult(False, f'Start script not found: {start_script}')

    return _run_arguments(['cmd.exe', '/c', str(start_script)], launch_path)


def control_server(
        action: str,
        server_name: str,
        launch_path: str,
        start_command: str = '',
        stop_command: str = '',
        restart_command: str = '') -> ControlResult:
    """Start, stop, or restart one configured Run8 server."""
    commands = {
        'start': start_command,
        'stop': stop_command,
        'restart': restart_command,
    }
    if action not in commands:
        return ControlResult(False, f'Unknown lifecycle action: {action}')

    if commands[action].strip():
        return _run_command(commands[action], launch_path)

    if action == 'start':
        return _start_windows_server(server_name, launch_path)
    if action == 'stop':
        return _stop_windows_server(server_name, launch_path)

    stop_result = (
        _run_command(stop_command, launch_path)
        if stop_command.strip()
        else _stop_windows_server(server_name, launch_path)
    )
    if not stop_result.success and 'No running server matching' not in stop_result.message:
        return stop_result

    start_result = (
        _run_command(start_command, launch_path)
        if start_command.strip()
        else _start_windows_server(server_name, launch_path)
    )
    if not start_result.success:
        return start_result

    return ControlResult(True, f'{stop_result.message}\n{start_result.message}')

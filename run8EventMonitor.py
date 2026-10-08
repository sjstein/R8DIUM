"""Read durable Run8 supervisor events and format administrator alerts."""

import json
from pathlib import Path


class EventCursor:
    """Read newline-delimited JSON events with a durable byte offset."""

    def __init__(self, event_path, state_path):
        self.event_path = Path(event_path)
        self.state_path = Path(state_path)
        self.offset = self._load_offset()

    def _load_offset(self):
        try:
            return max(0, int(self.state_path.read_text(encoding='ascii').strip()))
        except (OSError, ValueError):
            return 0

    def read_pending(self):
        try:
            size = self.event_path.stat().st_size
        except OSError:
            return []
        if self.offset > size:
            self.offset = 0

        pending = []
        with self.event_path.open('rb') as stream:
            stream.seek(self.offset)
            while True:
                line = stream.readline()
                if not line:
                    break
                if not line.endswith(b'\n'):
                    break
                next_offset = stream.tell()
                try:
                    event = json.loads(line.decode('utf-8'))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    event = None
                pending.append((event, next_offset))
        return pending

    def commit(self, offset):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(self.state_path.suffix + '.tmp')
        temporary.write_text(str(offset) + '\n', encoding='ascii')
        temporary.replace(self.state_path)
        self.offset = offset


def format_unexpected_exit(event):
    details = [
        '**Run8 restarted automatically after a crash**',
        'Cause: unexpected exit of Run8; the supervisor started it again.',
        f"Time: `{event.get('timestamp_utc', 'unknown')}`",
        f"Launcher exit status: `{event.get('exit_status', 'unknown')}`",
    ]
    if event.get('memory_available'):
        details.append(f"Host memory available: `{event['memory_available']}`")
    if event.get('swap_free'):
        details.append(f"Host swap free: `{event['swap_free']}`")
    if event.get('cgroup_oom_kill') is not None:
        details.append(f"Container OOM kills: `{event['cgroup_oom_kill']}`")
    if event.get('diagnostic_file'):
        details.append(f"Private diagnostic: `{event['diagnostic_file']}`")
    details.append('A separate notification will follow when Auto Dispatcher (Otto) is engaged.')
    return '\n'.join(details)


def format_otto_engaged(event):
    return '\n'.join([
        '**Run8 startup complete: Auto Dispatcher engaged**',
        'Auto Dispatcher (Otto) is active on all signaled routes.',
        f"Time: `{event.get('timestamp_utc', 'unknown')}`",
        f"Activation attempt: `{event.get('attempt', 'unknown')}`",
    ])


def format_otto_failure(event):
    details = [
        '**Run8 requires attention: Auto Dispatcher was not engaged**',
        f"Time: `{event.get('timestamp_utc', 'unknown')}`",
        f"Reason: `{event.get('error', 'unknown')}`",
    ]
    if event.get('diagnostic_file'):
        details.append(f"Private screenshot: `{event['diagnostic_file']}`")
    return '\n'.join(details)


def format_supervisor_event(event):
    formatters = {
        'unexpected_exit': format_unexpected_exit,
        'otto_engaged': format_otto_engaged,
        'otto_activation_failed': format_otto_failure,
    }
    formatter = formatters.get(event.get('event'))
    return formatter(event) if formatter else None


def format_manual_restart(server_name, actor, control_message):
    return '\n'.join([
        '**Run8 restarted by a Discord administrator**',
        f'Server: `{server_name}`',
        f'Requested by: {actor}',
        'Cause: Manual `/restart_server` command.',
        f'Control response: {control_message}',
        'A separate notification will follow when Auto Dispatcher (Otto) is engaged.',
    ])

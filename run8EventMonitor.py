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
        '**Run8 restarted after an unexpected exit**',
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
    details.append('The supervisor has started Run8 again. Auto Dispatcher may need attention.')
    return '\n'.join(details)

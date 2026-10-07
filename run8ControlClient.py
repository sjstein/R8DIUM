#!/usr/bin/env python3
#########################
# R8DIUM : Run8 Database for Integrated User Management
##########################
"""Client for the private Run8 supervisor Unix socket."""

import argparse
import json
import os
import socket
import sys


DEFAULT_SOCKET_PATH = '/run8-control/control.sock'
MAX_RESPONSE_BYTES = 8192


def send_command(action: str, socket_path: str = DEFAULT_SOCKET_PATH) -> dict:
    request = json.dumps({'action': action}).encode('utf-8') + b'\n'
    response = bytearray()

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(10)
        client.connect(socket_path)
        client.sendall(request)
        while len(response) < MAX_RESPONSE_BYTES:
            chunk = client.recv(min(4096, MAX_RESPONSE_BYTES - len(response)))
            if not chunk:
                break
            response.extend(chunk)
            if b'\n' in chunk:
                break

    if not response:
        raise RuntimeError('Run8 supervisor returned an empty response.')
    return json.loads(response.split(b'\n', 1)[0].decode('utf-8'))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Control the local Run8 supervisor.')
    parser.add_argument('action', choices=('start', 'stop', 'restart', 'status'))
    parser.add_argument(
        '--socket',
        default=os.environ.get('RUN8_CONTROL_SOCKET', DEFAULT_SOCKET_PATH),
        help='Path to the supervisor Unix socket.',
    )
    args = parser.parse_args(argv)

    try:
        response = send_command(args.action, args.socket)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f'Unable to contact Run8 supervisor: {error}', file=sys.stderr)
        return 2

    print(response.get('message', 'Run8 supervisor returned no message.'))
    return 0 if response.get('ok') else 1


if __name__ == '__main__':
    raise SystemExit(main())

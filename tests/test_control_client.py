import contextlib
import io
import unittest
from unittest import mock

import run8ControlClient


class ControlClientTests(unittest.TestCase):
    @mock.patch('run8ControlClient.send_command')
    def test_success_response_returns_zero(self, send_command):
        send_command.return_value = {'ok': True, 'message': 'Run8 stopped.'}
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            status = run8ControlClient.main(['stop', '--socket', '/tmp/control.sock'])

        self.assertEqual(status, 0)
        self.assertEqual(output.getvalue().strip(), 'Run8 stopped.')
        send_command.assert_called_once_with('stop', '/tmp/control.sock')

    @mock.patch('run8ControlClient.send_command')
    def test_supervisor_error_returns_one(self, send_command):
        send_command.return_value = {'ok': False, 'message': 'Unable to start Run8.'}
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            status = run8ControlClient.main(['start'])

        self.assertEqual(status, 1)


if __name__ == '__main__':
    unittest.main()

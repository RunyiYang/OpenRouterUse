import base64
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch

import use_token


class TokenClientTests(unittest.TestCase):
    def test_token_alone_uses_bundled_address_without_config_file(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'DISTRIBUTION_API_KEY': 'gw_' + 'a' * 43}, clear=True):
            path = Path(directory) / '.env.client'
            base, token = use_token.configuration(path)
            self.assertEqual(base, use_token.DEFAULT_BASE_URL)
            self.assertEqual(token, 'gw_' + 'a' * 43)
            self.assertFalse(path.exists())

    def test_first_use_prompts_once_and_saves_private_token(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True), patch.object(use_token.getpass, 'getpass', return_value='gw_' + 'a' * 43) as prompt, patch('builtins.print'):
            path = Path(directory) / '.env.client'
            first = use_token.configuration(path, interactive=True)
            second = use_token.configuration(path, interactive=True)
            self.assertEqual(first, second)
            self.assertEqual(prompt.call_count, 1)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertNotIn('DISTRIBUTION_BASE_URL', path.read_text())

    def test_invalid_pasted_token_is_not_saved(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True), patch.object(use_token.getpass, 'getpass', return_value='wrong'):
            path = Path(directory) / '.env.client'
            with self.assertRaises(ValueError):
                use_token.configuration(path, interactive=True)
            self.assertFalse(path.exists())

    def test_dedicated_env_and_environment_override(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = Path(directory) / '.env.client'
            path.write_text('DISTRIBUTION_BASE_URL=http://127.0.0.1:8766/v1\nDISTRIBUTION_API_KEY=gw_' + 'a' * 43)
            self.assertEqual(use_token.configuration(path)[1], 'gw_' + 'a' * 43)
            os.environ['DISTRIBUTION_API_KEY'] = 'gw_' + 'b' * 43
            self.assertEqual(use_token.configuration(path)[1], 'gw_' + 'b' * 43)
            os.environ['DISTRIBUTION_BASE_URL'] = 'http://user:password@host/v1'
            with self.assertRaises(ValueError):
                use_token.configuration(path)

    def test_image_response_saved_and_existing_file_preserved(self):
        raw = b'\x89PNG\r\n\x1a\nexample'
        response = {'data': [{'b64_json': base64.b64encode(raw).decode(), 'mime_type': 'image/png'}]}
        with tempfile.TemporaryDirectory() as directory:
            basename = Path(directory) / 'result'
            paths = use_token.save_images(response, basename)
            self.assertEqual(paths[0].read_bytes(), raw)
            with self.assertRaises(FileExistsError):
                use_token.save_images(response, basename)

    def test_redirect_is_not_followed_and_auth_reaches_only_target(self):
        calls = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                calls.append((self.path, self.headers.get('Authorization')))
                self.send_response(302)
                self.send_header('Location', '/should-not-receive-key')
                self.end_headers()

        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with self.assertRaisesRegex(ValueError, 'HTTP 302'):
                use_token.call('http://127.0.0.1:' + str(server.server_port) + '/v1', 'gw_example', '/models')
            self.assertEqual(calls, [('/v1/models', 'Bearer gw_example')])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_cli_routes_text_and_image_requests(self):
        with patch.object(use_token, 'configuration', return_value=('http://host/v1', 'gw_test')), patch.object(use_token, 'call') as call, patch('builtins.print'):
            call.return_value = {'choices': [{'message': {'content': 'OK'}}]}
            self.assertEqual(use_token.main(['chat', 'Hello']), 0)
            self.assertEqual(call.call_args.args[2], '/chat/completions')
            self.assertEqual(call.call_args.args[3]['model'], use_token.TEXT_MODEL)
            with patch.object(use_token, 'save_images', return_value=[]):
                self.assertEqual(use_token.main(['image', 'A dog', '--aspect-ratio', '1:1']), 0)
            self.assertEqual(call.call_args.args[2], '/images/generations')
            self.assertEqual(call.call_args.args[3]['aspect_ratio'], '1:1')

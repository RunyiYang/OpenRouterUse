#!/usr/bin/env python3
"""Use a distributed Gemini token. Python 3.9+, no package installation needed."""
import argparse
import base64
import getpass
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

TEXT_MODEL = 'google-ai-studio/gemini-2.5-flash'
IMAGE_MODEL = 'gemini-2.5-flash-image'
DEFAULT_BASE_URL = 'http://10.126.166.98:8766/v1'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def configuration(path, interactive=False):
    values = {}
    path = Path(path)
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, separator, value = line.partition('=')
            if separator and key.strip() in ('DISTRIBUTION_BASE_URL', 'DISTRIBUTION_API_KEY'):
                values[key.strip()] = value.strip().strip('"\'')
    # These dedicated variables never load the administrator's upstream .env.
    values.update({key: os.environ[key] for key in ('DISTRIBUTION_BASE_URL', 'DISTRIBUTION_API_KEY') if key in os.environ})
    base = values.get('DISTRIBUTION_BASE_URL', DEFAULT_BASE_URL).rstrip('/')
    token = values.get('DISTRIBUTION_API_KEY', '')
    url = urlsplit(base)
    if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password or url.query or url.fragment or url.path != '/v1':
        raise ValueError('Set DISTRIBUTION_BASE_URL in .env.client to the service address provided to you, ending in /v1.')
    first_use = not path.exists() and not token and interactive
    if first_use:
        token = getpass.getpass('First use: paste your token (input is hidden): ').strip()
    if not re.fullmatch(r'gw_[A-Za-z0-9_-]{32,80}', token):
        raise ValueError('A valid token starting with gw_ is required. Run python3 use_token.py models in a terminal and paste your token, or set DISTRIBUTION_API_KEY.')
    if first_use:
        # Save only this recipient's token; do not overwrite any existing configuration.
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write('DISTRIBUTION_API_KEY=' + token + '\n')
        print('Token saved to ' + str(path) + '. You will not need to enter it again.', file=sys.stderr)
    return base, token


def call(base, token, path, payload=None):
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}
    data = None
    if payload is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    request = Request(base + path, headers=headers, data=data)
    # Never forward credentials to a redirect target; do not automatically retry inference.
    try:
        with build_opener(NoRedirect()).open(request, timeout=150) as response:
            return json.load(response)
    except HTTPError as error:
        messages = {401: 'The token is invalid, paused, or revoked.', 403: 'The model or your network is not allowed for this token.',
                    429: 'Too many requests or simultaneous calls. Try again later.', 502: 'The provider request failed. Check usage before deciding whether to retry.',
                    503: 'The service is busy or unavailable. Contact your token provider.'}
        raise ValueError('HTTP ' + str(error.code) + ': ' + messages.get(error.code, 'The request failed. Check the address, model, and request parameters.')) from None
    except (URLError, TimeoutError, OSError):
        raise ValueError('Connection failed or timed out. Check network access, service availability, and the Base URL. Check usage before retrying.') from None


def save_images(response, basename):
    images = response.get('data') or []
    if not images:
        raise ValueError('The response contained no images.')
    saved = []
    for index, item in enumerate(images):
        ext = {'image/png': '.png', 'image/jpeg': '.jpg', 'image/webp': '.webp'}.get(item.get('mime_type', 'image/png'))
        if ext is None:
            raise ValueError('Unsupported image format.')
        raw = base64.b64decode(item['b64_json'], validate=True)
        if not raw:
            raise ValueError('The image data is empty.')
        path = Path(str(basename) + ('' if len(images) == 1 else '_' + str(index + 1)) + ext)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Preserve existing files; select another --out basename to run again.
        with path.open('xb') as stream:
            stream.write(raw)
        saved.append(path)
    return saved


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env', default='.env.client', help='configuration file (default: .env.client)')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('models', help='list models available to your token without running inference')
    commands.add_parser('usage', help='show monthly usage and estimated costs for your token')
    chat = commands.add_parser('chat', help='send one text generation request')
    chat.add_argument('prompt')
    chat.add_argument('-m', '--model', default=TEXT_MODEL)
    chat.add_argument('--max-tokens', type=int, default=1024)
    image = commands.add_parser('image', help='send one image generation request and save the image')
    image.add_argument('prompt')
    image.add_argument('-m', '--model', default=IMAGE_MODEL)
    image.add_argument('--aspect-ratio', default=None)
    image.add_argument('-o', '--out', default='outputs/image-' + datetime.now().strftime('%Y%m%d-%H%M%S'), help='output filename prefix, without an extension')
    args = parser.parse_args(argv)
    try:
        base, token = configuration(args.env, interactive=sys.stdin.isatty())
        if args.command == 'models':
            for model in call(base, token, '/models')['data']:
                print(model['id'], 'Image' if model.get('route') == 'native' else 'Text', sep='\t')
        elif args.command == 'usage':
            print(json.dumps(call(base, token, '/usage'), ensure_ascii=False, indent=2))
        elif args.command == 'chat':
            result = call(base, token, '/chat/completions', {'model': args.model, 'messages': [{'role': 'user', 'content': args.prompt}], 'max_tokens': args.max_tokens})
            print(result['choices'][0]['message']['content'])
            print('Usage: ' + json.dumps(result.get('usage', {})), file=sys.stderr)
        else:
            payload = {'model': args.model, 'prompt': args.prompt, 'response_format': 'b64_json'}
            if args.aspect_ratio:
                payload['aspect_ratio'] = args.aspect_ratio
            result = call(base, token, '/images/generations', payload)
            for path in save_images(result, args.out):
                print('Saved: ' + str(path.resolve()))
            print('Usage: ' + json.dumps(result.get('usage', {})), file=sys.stderr)
    except (EOFError, KeyboardInterrupt):
        print('\nCancelled. Check usage before retrying any request.', file=sys.stderr)
        return 130
    except (ValueError, KeyError, IndexError, TypeError, OSError) as error:
        if isinstance(error, FileExistsError):
            message = 'An output image already exists. Choose a different --out filename prefix.'
        elif isinstance(error, ValueError):
            message = str(error)
        else:
            message = 'Could not read the configuration or response, or save the image. Check your configuration and output path.'
        print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

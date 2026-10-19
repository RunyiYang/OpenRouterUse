# Client tests

Run these commands from the repository root:

```bash
python3 -m unittest discover -s tests -p test_token_client.py -v
python3 -m py_compile use_token.py
```

The seven offline tests require no real token, do not read your configuration, and do not call a model. They use temporary files, mocked responses, and a temporary local HTTP server to cover:

- Using the built-in service address when only a token is provided.
- Saving a token with file permissions `600` on first use, without prompting again.
- Rejecting invalid token formats without saving them.
- Configuration and environment variable precedence, and invalid address checks.
- Decoding and saving images without overwriting existing files.
- Rejecting HTTP redirects to avoid forwarding credentials to another address.
- Sending text and image commands to the correct endpoints with the correct parameters.

GitHub Actions runs the same offline tests on Python 3.9, 3.12, and 3.13.

## Check a real connection

Once you have a token, run:

```bash
python3 use_token.py models
python3 use_token.py usage
```

On first use, paste your token at the terminal prompt. These commands do not run inference.

To test actual generation, run the following commands manually. Each sends one model request and may incur costs; they are not part of the default tests:

```bash
python3 use_token.py chat "Reply with exactly OK."
python3 use_token.py image "A simple blue circle on a white background."
```

The text command should return a nonempty reply. The image command should save a readable image in `outputs/`. Your computer must be able to reach the service's network. If a request fails or times out, check `usage` before deciding whether to retry.

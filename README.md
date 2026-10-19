# OpenRouterUse

Use your token to call Gemini text and image models from Python. **All you need is your token and this repository.** The service address is built in, and no third-party Python packages are required.

## Quick start

Install Python 3.9+ and Git, then run these commands in your terminal:

```bash
git clone https://github.com/RunyiYang/OpenRouterUse.git
cd OpenRouterUse
python3 use_token.py models
```

When you see this prompt, **paste your complete token into the terminal and press Enter**:

```text
First use: paste your token (input is hidden):
```

Nothing appears while you type or paste. This is normal. Your token is saved to `.env.client`, so you only need to enter it once. On Windows, you can use `py` instead of `python3`.

The command lists the models available to your token. Your computer must be able to reach the service's local network, and the service must be online. A token alone does not provide network access.

## Text generation

```bash
python3 use_token.py chat "Hello! Introduce yourself."

# Choose a model and an output limit
python3 use_token.py chat "Write a short poem" \
  -m google-ai-studio/gemini-3.5-flash --max-tokens 1024
```

Default text model: `google-ai-studio/gemini-2.5-flash`. The default output limit is 1024 tokens.

## Image generation

```bash
python3 use_token.py image "a portrait of a sheepadoodle wearing a cape"

# Choose a model, aspect ratio, and output filename prefix
python3 use_token.py image "A coastline at sunset" \
  -m gemini-3.1-flash-image --aspect-ratio 16:9 -o outputs/coast
```

Default image model: `gemini-2.5-flash-image`. Images are saved to `outputs/`, with an extension matching the returned format. Existing files are never overwritten; choose another `--out` prefix if needed.

## Models and usage

```bash
# List models available to your token
python3 use_token.py models

# View your token's usage and estimated costs for the current month
python3 use_token.py usage
```

These models were verified through this service on October 19, 2026. Run `models` to check your token's permissions; availability can change.

| Type | Model ID |
| --- | --- |
| Text | `google-ai-studio/gemini-4-argon` |
| Text | `google-ai-studio/gemini-3.5-flash` |
| Text | `google-ai-studio/gemini-3.5-flash-lite` |
| Text | `google-ai-studio/gemini-2.5-flash` |
| Text | `google-ai-studio/gemini-2.5-pro` |
| Image | `gemini-2.5-flash-image` |
| Image | `gemini-3-pro-image` |
| Image | `gemini-3.1-flash-image` |
| Image | `gemini-3.1-flash-lite-image` |
| Image | `gemini-nano-banana-2.1` |

Text model IDs include the `google-ai-studio/` prefix. Image model IDs do not. The service supports non-streaming text chat and text-to-image generation. Tool calls, image inputs or editing, audio, and video are not supported.

## Troubleshooting

| Question or error | What to do |
| --- | --- |
| Where do I paste my token? | Run `python3 use_token.py models` and paste it at the terminal prompt, then press Enter |
| Why is my input invisible? | Token input is hidden; paste the token and press Enter |
| Connection failed | Check that your network can reach the service; ask your token provider if the address has changed |
| HTTP 401 | Check that your token is complete and active, or contact your token provider |
| HTTP 403 | Run `models` to check model access, and confirm that your network is allowed |
| HTTP 429 | Reduce your request rate or the number of simultaneous requests |
| HTTP 502 or timeout | Check `usage` first; failed requests may still incur usage, and the client does not retry automatically |

Keep your token and `.env.client` private. Never commit them to GitHub. Each `chat` or `image` command sends one real inference request and may incur costs. `models` and `usage` do not run inference. Costs are estimates based on OpenRouter's public prices, not the provider's actual bill; unknown costs are not treated as confirmed zero charges.

More details: [Python integration, HTTP examples, and configuration](docs/TOKEN_CLIENT.md) | [Client tests](docs/TESTING.md).

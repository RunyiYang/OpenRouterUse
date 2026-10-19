# Token client guide

You need a `gw_...` token from your token provider and a clone of this repository. The service address is built in, so you do not need to enter a Base URL or create a configuration file first. This token works with this Gemini service; it cannot be used directly on OpenRouter's website.

## Quick start

```bash
git clone https://github.com/RunyiYang/OpenRouterUse.git
cd OpenRouterUse
python3 use_token.py models
```

On first use in a terminal, paste your token at the prompt and press Enter. Input is hidden. The client saves it to `.env.client` automatically. You can then run:

```bash
python3 use_token.py chat "Explain machine learning in one sentence"
python3 use_token.py chat "Write a short poem" -m google-ai-studio/gemini-3.5-flash --max-tokens 1024
python3 use_token.py image "a portrait of a sheepadoodle wearing a cape"
python3 use_token.py image "A tiny house by the sea" -m gemini-3.1-flash-image --aspect-ratio 16:9 -o outputs/coast
python3 use_token.py usage
```

Python 3.9+ is required, with no additional packages. On Windows, use `py` instead of `python3`. Your computer must have network access to the service, and the service must be online. The built-in address is `http://10.126.166.98:8766/v1`; it is a private network address, not a public internet endpoint.

### Optional: scripts and manual configuration

For non-interactive scripts, set the `DISTRIBUTION_API_KEY` environment variable. No address configuration is required. A manual `.env.client` file also only needs one line:

```dotenv
DISTRIBUTION_API_KEY=gw_REPLACE_WITH_YOUR_DISTRIBUTED_TOKEN
```

Existing configuration files are preserved rather than overwritten. To replace a saved token, edit the `DISTRIBUTION_API_KEY` line in `.env.client`.

If your token provider changes the service address, set `DISTRIBUTION_BASE_URL` to override the built-in address. Environment variables take precedence over the configuration file. Use `python3 use_token.py --env /path/to/config models` to read a different configuration file. The client does not read `.env`.

Images are saved to timestamped files in `outputs/`, or to your chosen `--out` prefix followed by `.png`, `.jpg`, or `.webp`. Existing files are never overwritten. Keep tokens and configuration files out of GitHub.

## Available models

The following models were verified through this service on October 19, 2026. Run `python3 use_token.py models` to check which are enabled for your token. Permissions and provider availability can change.

| Type | Exact model ID |
| --- | --- |
| Text | `google-ai-studio/gemini-4-argon` |
| Text | `google-ai-studio/gemini-3.5-flash` |
| Text | `google-ai-studio/gemini-3.5-flash-lite` |
| Text (default) | `google-ai-studio/gemini-2.5-flash` |
| Text | `google-ai-studio/gemini-2.5-pro` |
| Image (default) | `gemini-2.5-flash-image` |
| Image | `gemini-3-pro-image` |
| Image | `gemini-3.1-flash-image` |
| Image | `gemini-3.1-flash-lite-image` |
| Image | `gemini-nano-banana-2.1` |

Keep the `google-ai-studio/` prefix for text models. Image model IDs have no prefix. Text models use Chat Completions; image models use the image endpoint or native Gemini `generateContent`. Do not send image models to the text endpoint.

## Use the client in your own project

Copy `use_token.py` into your project. It only uses the Python standard library. After saving your token or setting `DISTRIBUTION_API_KEY`, you can call it from Python:

```python
from use_token import configuration, call, save_images

base_url, token = configuration('.env.client')
result = call(base_url, token, '/chat/completions', {
    'model': 'google-ai-studio/gemini-2.5-flash',
    'messages': [{'role': 'user', 'content': 'Hello'}],
    'max_tokens': 1024,
})
print(result['choices'][0]['message']['content'])

result = call(base_url, token, '/images/generations', {
    'model': 'gemini-2.5-flash-image',
    'prompt': 'a portrait of a sheepadoodle wearing a cape',
    'response_format': 'b64_json',
})
print(save_images(result, 'outputs/my-image'))
```

Other backend clients that support Chat Completions can use Base URL `http://10.126.166.98:8766/v1` and your distributed token as their API key. Disable streaming and tool calls. The service currently accepts text inputs only; image inputs or editing, files, audio, video, multiple candidates, and tool calls are not supported.

### HTTP / curl

Replace the token placeholder below with your own token. If your token provider gives you a new address, update the Base URL too:

```bash
export DISTRIBUTION_BASE_URL=http://10.126.166.98:8766/v1
export DISTRIBUTION_API_KEY=gw_REPLACE_WITH_YOUR_TOKEN

curl "$DISTRIBUTION_BASE_URL/models" \
  -H "Authorization: Bearer $DISTRIBUTION_API_KEY"

curl "$DISTRIBUTION_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $DISTRIBUTION_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"model":"google-ai-studio/gemini-2.5-flash","messages":[{"role":"user","content":"Hello"}],"max_tokens":1024}'

curl "$DISTRIBUTION_BASE_URL/images/generations" \
  -H "Authorization: Bearer $DISTRIBUTION_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"model":"gemini-2.5-flash-image","prompt":"a dog in a cape","response_format":"b64_json"}' \
  -o image-response.json

curl "$DISTRIBUTION_BASE_URL/usage" \
  -H "Authorization: Bearer $DISTRIBUTION_API_KEY"
```

Image responses contain `data[].b64_json` and `mime_type`, not download URLs. The included client decodes and saves them automatically. Decode the base64 yourself when using raw HTTP requests.

For the native Gemini image protocol, use the root address without `/v1`, for example `http://10.126.166.98:8766/v1beta/models/gemini-2.5-flash-image:generateContent`. Send your token in the `x-goog-api-key` header, with text in `contents[].parts[].text`. Returned images are in `candidates[].content.parts[].inlineData`. Both image interfaces count toward the same token's usage.

## Usage, costs, and troubleshooting

The service monitors usage without a budget, token, or monthly request cap. Default operating limits are 30 requests per minute and two simultaneous requests, although your token may have different limits. A single request allows 1-8192 output tokens and a JSON body of up to 64 KiB, with an additional combined input-size check.

`usage` returns statistics for your token for the current UTC calendar month. `estimated_usd` is a reference estimate based on OpenRouter's public prices and the usage returned by the provider. It is not an actual provider bill. If `unknown_cost` is greater than zero, some costs are still unconfirmed, so the estimate is incomplete. The legacy fields `reserved_usd` and `held_tokens` describe conservative estimates for unconfirmed calls; they do not freeze funds or consume a quota.

| Error or symptom | What to do |
| --- | --- |
| Connection failed | Check the Base URL, network access, and whether the service is online |
| 401 | Ask your token provider to confirm that the token is complete, active, and not revoked |
| 403 | Check model permissions with `models` and confirm network access |
| 400 | Check the model prefix, output length, and parameters; do not enable streaming or tools |
| 429 | Reduce request frequency or concurrency; this is not a budget error |
| 502 or timeout | The provider may already have processed the request; check `usage` before retrying |
| Browser frontend cannot connect | Use a backend or script; cross-origin browser requests are rejected. Do not embed your token in a public webpage |

`models` and `usage` do not run inference. Each `chat` or `image` command sends one real request and may incur costs. The client never retries inference automatically.

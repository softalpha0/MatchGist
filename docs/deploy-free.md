# Deploying MatchGist for free (no Azure account)

Use this if you can't open an Azure subscription. Nothing here needs a card.

| Piece | Free option | Notes |
|---|---|---|
| Model for the agents | Any OpenAI-compatible free tier, e.g. **Groq** | Same Microsoft Agent Framework client, pointed at another `base_url` |
| Hosting | **Hugging Face Spaces**, Docker, CPU basic | Builds our `Dockerfile`; sleeps when idle and wakes on the next visit |
| Voice | none | Voice notes show the transcript and an estimated size |

Free tiers change often. Check the provider's own limits page before relying on the numbers below.

## 1. Model key (Groq example)

1. Sign up at https://console.groq.com and create an API key.
2. Pick a model from its model list (a small, fast chat model is best: the agents have an 8 s timeout).
3. Put it in your local `.env` (never committed):
   ```
   MATCHGIST_LLM_BASE_URL=https://api.groq.com/openai/v1
   MATCHGIST_LLM_API_KEY=<key>
   MATCHGIST_LLM_MODEL=<model id>
   MATCHGIST_LLM_CALLS_PER_MINUTE=60
   MATCHGIST_LLM_CALLS_PER_DAY=900
   ```
4. Restart `uvicorn` and open `http://127.0.0.1:8000/config`: `llm_mode` should say `openai-compatible`.

**Why the caps.** A full match makes about 95 model calls of roughly 600 tokens each. Free tiers limit requests
and tokens per minute and per day. Calls over our cap skip the model and use the templates at once, so the feed
never waits on a 429, and a public link can't burn the day's quota. The System panel says when that happens.

One goal triggers about 12 calls at once (the Explainer, then a Localizer and Compressor per fan), so a cap
below ~60 a minute turns most of a match into templates. At 60x a match lasts about 1.5 minutes (~60 calls a
minute), so the live page now starts at **30x**; record the demo at 10x or 30x to show model output throughout.

Gemini (Google AI Studio) and OpenRouter `:free` models also expose OpenAI-compatible endpoints; only the three
`MATCHGIST_LLM_*` values change.

## 2. Hugging Face Space

1. Create an account at https://huggingface.co, then **New Space**: SDK **Docker**, template **Blank**, hardware
   **CPU basic (free)**, visibility **Public**. Name it e.g. `matchgist`.
2. Space → **Settings** → **Variables and secrets**:
   - variables: `MATCHGIST_LLM_BASE_URL`, `MATCHGIST_LLM_MODEL`, `MATCHGIST_LLM_CALLS_PER_MINUTE`,
     `MATCHGIST_LLM_CALLS_PER_DAY`
   - **secret**: `MATCHGIST_LLM_API_KEY`
3. Create a Hugging Face **access token** with write access (Settings → Access Tokens).
4. Commit your work, then from the repo root in PowerShell:
   ```powershell
   .\infra\deploy-hf.ps1 -Space <your-hf-username>/matchgist
   ```
   Git asks for a username and password: use your Hugging Face username and the token.
   The script pushes only committed files (never `.env`) and adds the Space header to
   the README copy it pushes.
5. Watch the build under the Space's **Logs** tab (a few minutes). Then open
   `https://<username>-matchgist.hf.space/live` (the Space page shows the exact URL under **Embed this Space**).
6. Check `/health` and `/config` on that URL. Put the URL in the README as the live demo.

To update after new commits, run the script again.

## Notes

- The Space sleeps after a period without visitors; the first visit after that takes about a minute while it
  starts. Open it yourself before recording and before the judging period.
- Live matches are in memory, as on Azure: one container serves every viewer.

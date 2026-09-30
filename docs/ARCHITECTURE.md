# BuildBot — Architecture and Development Guide

## What this is

BuildBot turns a research paper (or a paragraph of prose) into a structured SRS,
then into a module checklist, then into working code. The pipeline is
`Paper → SRS → Modules → Code`, and each stage is driven by a pluggable LLM
provider so the same code works against Ollama, OpenRouter, OpenAI or any
OpenAI-compatible endpoint.

## Layout

```
api/python/          FastAPI service
  main.py            app + request models + routes
  llm_client.py      LLMClient: provider dispatch, key resolution
  collabuild_utils.py SRS generation and module parsing (pure functions)
  agent_reach_utils.py  outbound fetch helpers
api/node/freebuff.js  Express worker wrapping the Freebuff CLI
frontend/            Next.js + Tailwind UI
tests/               pytest suite for the pure helpers
main.py              root entry point: `python main.py`
```

`api/python/main.py` imports its siblings flat (`from llm_client import
LLMClient`), so that directory must be on `sys.path`. The root `main.py`
inserts it before importing the app; `pyproject.toml` does the same for tests
via `pythonpath = ["api/python"]`.

## Running

```bash
# 1. Python API
pip install -r api/python/requirements.txt
python main.py                 # 127.0.0.1:8000
python main.py --reload

# 2. Next.js frontend (separate terminal)
cd frontend
npm install
npm run dev                    # http://localhost:3000
```

The Node worker is optional and only needed when the Freebuff CLI is available:

```bash
cd api/node && npm install && npm start
```

## Configuration

Provider selection is per-request (`provider`, `model`, `api_key`, `base_url`).
When `api_key` is omitted, `llm_client.LLMClient._get_env_key()` falls back to
the environment. `python-dotenv` is a dependency, so a local `.env` is picked up
automatically. Do not commit `.env`.

## Tests

```bash
python -m pytest tests -q
```

The suite covers `collabuild_utils` — SRS generation, module parsing, the
module-section keyword heuristic, and the default-module fallback. Those
functions are pure, so the tests need no network, no LLM and no database.
LLM-backed and network-backed paths are not unit tested; exercise those against
a running provider.

## Deployment

`netlify.toml` and `vercel.json` configure the frontend. The Python API and the
Node worker each need their own host; neither is covered by those two files.

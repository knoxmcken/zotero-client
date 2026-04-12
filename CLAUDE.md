# CLAUDE.md — AI Assistant Guide for zotero-client

This file provides context for AI assistants working in this repository.

## Project Overview

`zotero-client` is a Python CLI application and library for managing Zotero bibliographic data. It wraps the Zotero REST API and exposes functionality via both a `zot` CLI command and a `ZoteroClient` Python class. Optional AI features (item summarization) integrate with the OpenAI API.

- **Package name:** `zotero-client`
- **Version:** 0.1.1
- **Python requirement:** >= 3.8
- **CLI entry point:** `zot` → `zotero_client.cli.main:main`

---

## Repository Structure

```
zotero-client/
├── zotero_client/          # Main Python package
│   ├── __init__.py         # Exports ZoteroClient
│   ├── api/
│   │   └── client.py       # ZoteroClient class — all HTTP/API logic
│   ├── cli/
│   │   └── main.py         # argparse CLI, uses Rich for output
│   ├── models/
│   │   ├── item.py         # Item dataclass + from_api_response()
│   │   ├── collection.py   # Collection dataclass + from_api_response()
│   │   └── tag.py          # Tag dataclass + from_api_response()
│   └── utils/
│       └── config.py       # load_config() — reads env vars / .env file
├── tests/
│   ├── test_client.py      # General ZoteroClient tests
│   ├── test_api/           # Per-feature API client tests
│   │   ├── test_client_items.py
│   │   ├── test_client_collections.py
│   │   ├── test_client_tags.py
│   │   ├── test_client_export.py
│   │   └── test_integration.py   # Marked @pytest.mark.integration
│   ├── test_cli/           # CLI command tests
│   │   ├── test_items.py
│   │   ├── test_export.py
│   │   └── test_configure.py
│   └── test_models/        # Data model tests
│       ├── test_item.py
│       └── test_collection.py
├── examples/
│   ├── basic_usage.py
│   └── jupyter/zotero_analysis.ipynb
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── FEATURES.md
│   └── IMPLEMENTATION_PLAN.md
├── .github/workflows/
│   └── integration-test.yml
├── pyproject.toml
├── requirements.txt
├── pytest.ini
├── .env.example
└── GEMINI.md               # Commit message conventions
```

---

## Architecture: Layered Design

The codebase follows a strict four-layer architecture. Respect these boundaries when adding features:

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **API** | `zotero_client/api/client.py` | HTTP calls, auth headers, response parsing — no business logic |
| **Models** | `zotero_client/models/` | Dataclasses with `from_api_response()` factory methods |
| **CLI** | `zotero_client/cli/main.py` | User input parsing (argparse), calls API/service layer, Rich formatting |
| **Utils** | `zotero_client/utils/config.py` | Environment/config loading |

- `ZoteroClient` in `api/client.py` is the **single point of contact** with the Zotero REST API (`https://api.zotero.org`).
- Models use Python `dataclasses`. Each model has a `from_api_response(data: dict)` classmethod.
- The CLI uses `argparse` (not `click`). Output is formatted using the `rich` library (tables, panels).
- `load_config()` in `utils/config.py` reads `ZOTERO_API_KEY`, `ZOTERO_USER_ID`, and `ZOTERO_LIBRARY_TYPE` from the environment or a `.env` file.

---

## Development Setup

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd zotero-client

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the package in editable mode (required for the `zot` CLI)
pip install -e .

# 4. Set up environment variables
cp .env.example .env
# Edit .env and fill in ZOTERO_API_KEY, ZOTERO_USER_ID, ZOTERO_LIBRARY_TYPE
```

**Required environment variables** (in `.env` or shell):
```
ZOTERO_API_KEY=<your-zotero-api-key>
ZOTERO_USER_ID=<your-zotero-user-id>
ZOTERO_LIBRARY_TYPE=users   # or 'groups'
```

**Optional:**
```
OPENAI_API_KEY=<your-openai-key>   # Only for AI summarization feature
```

---

## Running Tests

```bash
# Unit tests only (no credentials needed) — default CI run
pytest tests/ -m "not integration"

# All tests including integration (requires .env with real credentials)
pytest tests/

# Specific test file
pytest tests/test_api/test_client_items.py -v

# With coverage
pytest tests/ --cov=zotero_client --cov-report=term
```

**Test markers** (defined in `pytest.ini`):
- `@pytest.mark.integration` — requires real Zotero API credentials; skipped in unit-only CI
- `@pytest.mark.slow` — for tests that are slow to run

**Testing conventions:**
- Unit tests use `unittest.mock` (`Mock`, `patch`, `MagicMock`) to avoid real HTTP calls.
- Patch `requests.get` / `requests.post` at the call site in `zotero_client.api.client`.
- Patch `load_config` (in `zotero_client.utils.config`) when testing CLI commands that call it.
- Use fixtures for constructing a `ZoteroClient` instance with fake credentials.
- Test files mirror the structure of the source: `test_api/` tests `api/`, `test_models/` tests `models/`, etc.

---

## CLI Usage Reference

```bash
# Items
zot items list [--limit N] [--search QUERY] [--type TYPE] [--tag TAG]
zot items get <item-id>

# Collections
zot collections list
zot collections get <collection-id>

# Tags
zot tags list

# Attachments
zot attachments list <item-id>
zot attachments download <attachment-id>

# Citations
zot citations get <item-id>

# AI features (requires OPENAI_API_KEY)
zot ai summarize <item-id>

# Duplicate detection
zot duplicates find

# Export / backup
zot export [--format FORMAT] [--output FILE]

# Configuration
zot configure
```

---

## Git Workflow

**Active branches:**
- `main` — stable, release-ready code
- `develop` — integration branch for new features
- Feature branches: `claude/...`, `feat/...`, etc.

**Commit message format** (from `GEMINI.md`):

```
<type>: <short imperative summary, max 50 chars>

<optional body: what and why, wrapped at 72 chars>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

**Examples:**
```
feat: Add tag filtering to items list command

fix: Mock load_config in export tests

docs: Update README with getting started section
```

For multi-line commits, write the message via a heredoc or `-m`:
```bash
git commit -m "$(cat <<'EOF'
feat: Implement duplicate detection for Zotero items

Compares items by title and creator fields to find duplicates.
EOF
)"
```

---

## CI/CD Pipeline

**Workflow:** `.github/workflows/integration-test.yml`

Triggers on push/PR to `main` and `develop`.

| Job | When | What |
|-----|------|------|
| `unit-tests` | Always | `pytest -m "not integration"` |
| `integration-tests` | After unit-tests pass | Full pytest suite + CLI smoke tests, with real credentials from GitHub Secrets |

**GitHub Secrets required for integration tests:**
- `ZOTERO_API_KEY`
- `ZOTERO_USER_ID`

---

## Key Conventions for AI Assistants

1. **Don't mix layers.** API HTTP logic belongs in `api/client.py`. Business logic belongs in services (or the client). CLI code only parses input and formats output.

2. **Use dataclasses for models.** Always add a `from_api_response(cls, data: dict)` classmethod to new models.

3. **Mock HTTP in unit tests.** Never make real network calls in non-integration tests. Patch `requests.get`/`requests.post` in `zotero_client.api.client`.

4. **Mock `load_config` in CLI tests.** CLI commands call `load_config()` at startup; patch it so tests don't require a `.env` file.

5. **Use Rich for CLI output.** All terminal output should use `rich` tables, panels, or `print`. Don't use bare `print()` for user-facing output.

6. **Follow conventional commits.** All commit messages must use a type prefix (`feat:`, `fix:`, `docs:`, etc.) with an imperative subject line.

7. **Run unit tests before committing.** `pytest tests/ -m "not integration"` must pass. Integration tests need real credentials and are only run in CI.

8. **Don't add a `services/` layer yet.** The architecture doc mentions a `services/` layer, but it hasn't been implemented — AI features are currently handled directly in `api/client.py`.

9. **The `.env` file is gitignored.** Never commit real credentials. Use `.env.example` as the template.

10. **Python >= 3.8 compatibility.** Avoid syntax or stdlib features that require Python 3.9+ (e.g., `dict | dict` union syntax, `list[str]` type hints in function signatures — use `List[str]` from `typing` instead).

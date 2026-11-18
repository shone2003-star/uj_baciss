# Service Delivery Reporter (Community Voice)

Citizens report local service problems (water, electricity, roads, sanitation, waste) by text, voice note and an optional photo, in English, isiZulu, isiXhosa, Afrikaans or Sesotho. AI agents triage the report, check the web for known outages, route it to a department, flag duplicates and draft a reply. Citizens sign in to submit and follow their own reports. An admin reviews: the report, then the reply. Nothing is ever sent.

All sample data is fictional. This is a teaching project, not a production system.

## What is needed

- Windows 11 with Git Bash, or macOS with zsh.
- [uv](https://docs.astral.sh/uv/), use the following command to install it on windows (using powershell): 
  ```powershell
      powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
- Node.js 
- Free API keys: Gemini (Google AI Studio), Groq and Tavily. LangSmith is optional.
- [Ollama](https://ollama.com/download) with a small model, for the privacy filter 

## The exact versions

This project was built and tested with these versions. Follow "Set up" below as written and you get them: the Python libraries come from `uv.lock` and the JavaScript libraries from `package-lock.json`, so you never type a library version yourself.

| Tool | Version | Where it is fixed |
|---|---|---|
| uv | 0.13.7 | the install command in step 1 |
| Python | 3.12.16 | `.python-version` (uv installs the patch release that goes with its own version, so use uv 0.13.7) |
| Node.js, npm | 24.22.1, 11.19.1 | install this Node.js yourself |
| Ollama | 0.40.16 | install yourself (the installer gives the newest; newer is fine) |
| Ollama model | `llama3.2:3b` | the tag in `ollama pull` |
| Python libraries | for example langgraph 1.2.21, langchain 1.5.0, fastapi 0.162.5, pydantic 2.14.3, chromadb 1.5.9, fastmcp 3.4.11, streamlit 1.67.0, langchain-ollama 1.1.0 | `uv.lock` |
| JavaScript libraries | Next.js 16.4.6, React 19.3.0, Tailwind CSS 4.3.3 | `frontend/package-lock.json` |

Two rules keep the versions the same:

- **Install with `uv sync --locked` and `npm ci`** (not `uv sync` alone and not `npm install`). `--locked` uses exactly what is in `uv.lock` and stops with an error if `pyproject.toml` and `uv.lock` disagree, instead of quietly choosing other versions. `npm ci` installs exactly what is in `package-lock.json`.
- **Do not upgrade anything** while you follow the course (no `uv lock --upgrade`, no `uv add`, no `npm update`). `fastmcp` is held below version 4 on purpose, because newer versions do not work with the other MCP library.

Keep `uv.lock` and `frontend/package-lock.json` with the project: they are what makes the versions the same for everyone.

## Set up

1. Install uv.

   Windows (run once in PowerShell):

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.13.7/install.ps1 | iex"
   ```

   macOS

   ```bash
   curl -LsSf https://astral.sh/uv/0.13.7/install.sh | sh
   ```

   Open a new terminal and check it: `uv --version` should say `uv 0.13.7`. If it shows another version, run the command above again.

2. From the project folder, install Python and the libraries:

   ```bash
   uv python install 3.12
   uv sync --locked
   ```

   Check the result (both should match the table above):

   ```bash
   uv run python --version
   uv pip list | grep -E "^(langgraph|langchain|fastapi|pydantic|chromadb|fastmcp|streamlit) "
   ```

   Expected: `Python 3.12.16`, then the library versions from the table. If `uv sync --locked` stops with an error that the lockfile needs to be updated, you changed `pyproject.toml` or `uv.lock`: restore them from the course files.

3. Create your key file and fill it in. `.env` is git-ignored; never commit it.

   ```bash
   cp .env.example .env
   ```

   Fill in the four keys that are switched on:

   | Variable | Used for | Where to get it |
   |---|---|---|
   | `GEMINI_API_KEY` | Triage, drafting, voice transcription | aistudio.google.com (API keys) |
   | `GROQ_API_KEY` | Routing, web check | console.groq.com/keys |
   | `TAVILY_API_KEY` | Web search | app.tavily.com |
   | `JWT_SECRET` | Signs login tokens | Make your own: `openssl rand -hex 32` |

   Lines that start with `#` are switched off. Take the `#` away when you want one. That is how you turn on LangSmith tracing and evals (`LANGSMITH_API_KEY`, `LANGSMITH_TRACING`, `LANGSMITH_PROJECT`; the key is at smith.langchain.com, under Settings, API Keys), switch the privacy model off (`PRIVACY_FILTER=false`) or try another model. Tracing sends report text to LangSmith's cloud, so use fictional data only.

4. Create the test accounts (see "Sign in" below):

   ```bash
   uv run python -m community_voice.auth.seed
   ```

5. Install Ollama and the model (see "Privacy filter" below).

6. Install the Next.js libraries and create its settings file. You do this once, and it needs Node.js 24.22.1:

   ```bash
   cd frontend
   npm ci
   cp .env.example .env.local
   cd ..
   ```

7. Check the setup (no keys or network needed):

   ```bash
   uv run pytest
   ```

## Run the app

With the setup done, start three servers, each in its own terminal and each from the project folder. Start the API first, because both screens talk to it.

| # | Server | What it is | Address |
|---|---|---|---|
| 1 | API | FastAPI, the brain of the app | http://127.0.0.1:8800 (docs at `/docs`) |
| 2 | Streamlit | the simple interface | http://localhost:8501 |
| 3 | Next.js | the full interface | http://localhost:3000 |

```bash
# Terminal 1: the API (start this one first)
uv run uvicorn community_voice.api.main:app --port 8800

# Terminal 2: Streamlit
uv run streamlit run app/streamlit_app.py

# Terminal 3: Next.js
cd frontend && npm run dev
```

Wait for `Application startup complete` in the first terminal. The first report you submit is slower than the rest, because it downloads a small search model (about 80 MB) once. Streamlit opens in your browser by itself. For Next.js, open http://localhost:3000: the login page has buttons that fill in the test accounts.

Ollama has to be running too, for the privacy filter. It starts by itself after you install it, so it needs no terminal. Check it with `curl http://localhost:11434`, which should answer `Ollama is running`.

Leave all three terminals open while you test, and stop each one with Ctrl+C. Restart the API after you pull changes or edit `.env`, so it picks them up.

To start again from nothing, stop the servers, delete `data/app.db`, `data/checkpoints.db` and `data/memory.db`, then run the seed command from step 4 to bring back the test accounts. This wipes every report.

The report details window uses `src/components/ui/dialog.tsx`, which is part of the code (built on Base UI, already a dependency), so there is nothing extra to install.

## Privacy filter

Before a report goes to any cloud service, a small model on your own computer removes names, street addresses, phone numbers, ID numbers and emails. Place names such as "Umlazi" stay, because routing needs them.

Install Ollama (Windows: download `OllamaSetup.exe` from https://ollama.com/download; macOS: `curl -fsSL https://ollama.com/install.sh | sh`). Then, in a new terminal:

```bash
ollama pull llama3.2:3b
```

Keep Ollama running while you use the app. It listens on `localhost:11434`.

- **Ollama not running:** the report is stopped and nothing is saved. The citizen can tick a box to continue anyway. Then only numbers and emails are removed, and names and addresses may reach the AI services.
- **PC too weak, or you do not want it:** add `PRIVACY_FILTER=false` to `.env` and restart the API. Numbers and emails are still removed; the local model is skipped.
- **Another model:** set `OLLAMA_MODEL` in `.env` (for example `llama3.2:1b`, lighter and less accurate).
- **Speed:** about 7 to 12 seconds more per report on a CPU-only PC; the first call after starting Ollama is slower while the model loads.
- **Limits:** it misses some names, especially in African languages, and it can remove a little too much. Voice notes are sent to Gemini for transcription *before* any redaction (Ollama cannot transcribe); the transcript is redacted before the workflow. Only the redacted text is stored.
- **Add places** the filter must keep in `data/knowledge_base/places.json`. Routing still knows only the areas in `directory.json`.
- **Score it** (needs Ollama running): `uv run python -m evals.run_privacy_evals`

## Conversations

A reply does not mean the problem is fixed. When the admin approves the reply, a **conversation** opens for that report, with the reply as its first message.

- **Citizen** (Messages page): reads the conversation, writes messages, and can press "Mark as fixed". That only flags it. After the admin closes the conversation it can still be read, but not written in.
- **Admin** (Conversations page): sees which conversations need attention (the citizen wrote last or marked it fixed), reads them, gets a **suggested reply** from the Chat Assistant (Gemini, using the policy documents), edits it and sends it. The assistant never sends anything. Only the admin closes a conversation.
- **Privacy:** a citizen's message goes through the same local privacy filter as a report (and the same consent tick if Ollama is not running). Only the redacted text is stored.
- **Limits:** 1000 characters a message, 50 messages a conversation. There are no emails or push messages: the pages refresh about every 15 seconds, or press Refresh in Streamlit.
- **All reports** (admin): a read-only list of every report in any status, including rejected ones. Click a row (Streamlit: select it, then "Show details") to open a **details window** with everything known about it: text, translation, urgency, routing, web check, review decisions and reply. The same window opens from the dashboard's urgent table and from a conversation.

## Review queue

The admin can sort the queue (most urgent, newest, oldest) and filter it by urgency, category and status. On the dashboard, an urgent report opens straight in the review queue. After you approve a review, the drafted reply takes about 7 to 15 seconds (two AI calls), and the screen says so while it works.

**If a step fails** (for example the AI service returns 503), the report is kept and marked **Stopped** in the queue. Open it and press **Retry**: the failed step runs again and the workflow carries on. This also works after the API was restarted in the middle of a run. A report that failed *before* it was saved is not kept: the citizen is told to send it again.

Suggestions can be wrong, for example by quoting a policy time that does not fit. Read them before you send.

## Sign in

The API needs a login. The seed command above creates three **test accounts**. Their passwords are public: use them for demos only.

| Role | Email | Password |
|---|---|---|
| Admin (reviews reports and drafts, sees the dashboard) | `admin@communityvoice.test` | `AdminPass123` |
| Citizen 1 (submits reports, sees only their own) | `citizen1@communityvoice.test` | `Citizen1Pass123` |
| Citizen 2 (submits reports, sees only their own) | `citizen2@communityvoice.test` | `Citizen2Pass123` |

In the Streamlit app, sign in on the first screen. A citizen follows their reports and reads the reply on the My Reports page, and talks to the municipality on the Messages page. The pages are the same for everyone, and the API refuses what the account may not do (a citizen opening the review queue gets "Admins only"). In the API docs page, use the Authorize button.

## Other things to run

- Notebooks: open `notebooks/` in VS Code and pick the project's `.venv` as the kernel. Clear the outputs before committing.
- Evals (scores triage and routing on 20 labelled reports):

  ```bash
  uv run python -m evals.run_evals --refresh
  ```

- Tests that call the real AI services: `uv run pytest -m live -s`
- Lint and format: `uv run ruff format` and `uv run ruff check`

## How a report moves

Privacy filter (local) → Triage (language, category, urgency) → Routing (municipality and department) → Context check (web search for known outages) → Duplicate check → Save → **Human review** → Drafter (reply from policy documents) → **Draft approval** → ready to send → **Conversation** with the citizen until the admin closes it.

## Folder guide

```
src/community_voice/     The application
  core/                  Settings (.env) and tracing setup
  auth/                  Password hashing, login tokens and the test-account seed
  schemas/               Pydantic models: the shape of data passed between steps
  llm/                   Which model (Gemini, Groq or local Ollama) each agent uses
  privacy/               The privacy filter: removes personal details before the cloud
  agents/                Triage, routing, context check, drafter and chat assistant agents
  tools/                 What the agents can call: directory lookup, policy search,
                         web search, duplicate search
  rag/                   Search indexes (Chroma): policy documents and past reports
  graph/                 The LangGraph workflow: state, steps, pauses for humans,
                         saved progress and long-term memory
  db/                    SQLite storage for reports, reviews, drafts and users
  media/                 Voice-note transcription and photo checks
  api/                   FastAPI endpoints and streaming of progress
  mcp_server/            The directory tools served over MCP (a demo; the app
                         does not need it)
app/                     Streamlit screens: sign in, submit, my reports, messages, review queue,
                         conversations, all reports, dashboard
frontend/                The Next.js app (TypeScript, Tailwind, shadcn/ui)
  src/app/               Routes only: login, then citizen and admin screens
  src/features/          One folder per feature: auth, reports, review, chat, history,
                         dashboard, runs (each with its API calls, schemas, hooks,
                         components)
  src/components/        Shared UI: ui (shadcn), layout, shared
  src/lib/               API client, stream reader, token store, helpers
  src/schemas/           zod schemas shared by features
data/
  knowledge_base/        Department directory, South African places and fictional policy documents
  sample_reports/        Sample reports, with voice recordings for the demo
  evals/                 The 20 labelled reports and the 12 privacy test reports
evals/                   Scoring code and the saved baseline scores
notebooks/               One notebook per concept: 01 to 12, 15 and 16 (the UI phases have none)
tests/                   unit/ runs offline; integration/ calls the real services
docs/teaching-log/       How each phase was built, with decisions and fixes
pyproject.toml, uv.lock  Libraries and tool settings (uv manages both)
.env.example             Template for your keys
```

Files created while you use the app and not committed: `data/app.db`, `data/checkpoints.db`, `data/memory.db` (reports, paused workflows, memory), `data/chroma/` (search indexes) and `data/uploads/` (photos).

## Good to know

- Voice notes are transcribed automatically and can be wrong, so the citizen always checks the text. isiZulu, isiXhosa, Sesotho and Setswana are experimental.
- On Gemini's free tier, Google may use what you send to improve its products. Use fictional data. The privacy filter lowers the risk but does not make data anonymous.
- The API runs on localhost only. Login covers two roles (citizen and admin); there is no registration, rate limiting or password reset.
- Free-tier models can return "503" or rate-limit errors at busy times. Wait a minute and try again. The chat assistant can take up to a minute.

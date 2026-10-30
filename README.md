# Life OS — Community Edition

A local personal planning app with a Chief of Staff, specialist agents, recurring goals, task check-ins, progress tracking, and user-confirmed memory.

This standalone edition includes a **FastAPI + SQLite backend** and a **Next.js web app**. It has no dependency on OpenAI Sites, Codex, Railway, or an existing cloud deployment. It contains generic examples, not an existing user's data or credentials. Licensed under [MIT](LICENSE).

## What works locally

- Plan, Progress, and Agents views, plus a top-right Settings screen.
- Ongoing goals without expiry, approved recurring routines, and check-in history.
- Light, Dark, and System appearance.
- Per-device recurring notification choices. Delivery requires the optional push setup below.
- Tenant-scoped SQLite records, progress calculations, and confirmed knowledge records.
- Optional live OpenAI Responses API conversations; without a key, agent chat returns a setup message and makes **no model calls**.

An initial install starts empty. The optional demo creates three synthetic goals so you can try the interface immediately.

## Requirements

- Python **3.11 or newer** (3.12 recommended), with `pip` and `venv`.
- Node.js **22.13 or newer**, with `npm`.
- Git and pnpm **11.25.0**. To install pnpm: `npm install --global pnpm@11.25.0`.
- Internet for the initial dependency installation. After that, the demo and deterministic tracking work locally; AI calls and connected services need internet.

## Quick start — macOS / Linux

### 1. Clone and install the backend

```bash
git clone https://github.com/pujagorai9/life-os-community.git
cd life-os-community
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
python scripts/bootstrap_private.py
```

No API key is needed for the first run. By default, `.env` stores the database at `private/life_os.db`. Your local data, attachments, profiles, and credentials are ignored by Git.

### 2. Optional: add synthetic demo goals

```bash
python scripts/seed_demo.py
```

This creates recurring learning, movement, and planning examples for tenant `me`. Running it again does not duplicate those goals. Skip this step if you prefer an empty database.

### 3. Start the API

From the repository root, with the virtual environment active:

```bash
life-os serve
```

Keep this terminal open. The API listens on **http://127.0.0.1:8000**.

- Health: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs

### 4. Start the web app in a second terminal

```bash
cd life-os-community/mobile
cp .env.example .env.local
pnpm install --frozen-lockfile
pnpm dev
```

Open **http://127.0.0.1:3000**. Both servers bind to loopback by default. Stop each with `Ctrl+C`.

## Windows / PowerShell

```powershell
git clone https://github.com/pujagorai9/life-os-community.git
cd life-os-community
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
.\.venv\Scripts\python.exe scripts\bootstrap_private.py
.\.venv\Scripts\python.exe scripts\seed_demo.py
.\.venv\Scripts\life-os.exe serve
```

In a second PowerShell terminal:

```powershell
cd life-os-community\mobile
Copy-Item .env.example .env.local
pnpm install --frozen-lockfile
pnpm dev
```

Using the virtual environment executables directly avoids changing PowerShell's script execution policy. Windows instructions are provided for the same Python/Node commands; the release smoke test was run on macOS.

## Your own goals and configuration

Edit `private/profile.toml` to set a display name, timezone, enabled agents, and privacy preferences. Use an IANA timezone such as `Europe/London` or `America/New_York`; set the same `LIFE_OS_TIMEZONE` in `.env` before generating demo schedules.

The web app currently focuses on viewing and tracking goals. Use `/docs` for the goal-creation and approval workflow:

1. `POST /v1/goals` with a tenant, life domain, owning specialist, success definition, metrics, and routines. Set `review_at` to `null` for an ongoing goal; give it a `timezone`.
2. `POST /v1/goals/{id}/approve?tenant_id=me` to activate the goal.
3. Inspect `GET /v1/goals/{id}/tracking-protocol?tenant_id=me`.
4. `POST /v1/goals/{id}/tracking-protocol/approval` with `{"tenant_id":"me","approved":true}` to approve recurring prompts.
5. Refresh the web app. Record task outcomes and inspect Progress.

`scripts/seed_demo.py` is also a small, complete Python example of that lifecycle. For a different tenant, update `NEXT_PUBLIC_LIFE_OS_TENANT_ID` in `mobile/.env.local`; rebuild/restart the web app after changing public environment variables.

Review dates on finite goals are cycle boundaries. Ongoing goals have no expiry, and reviews do not automatically pause them. Schedule your own weekly/monthly review in a calendar; this public edition does not create meetings automatically.

## Optional live AI

Set these **in your local root `.env`**, using your own OpenAI API account:

```dotenv
OPENAI_API_KEY=your-own-api-key
LIFE_OS_MODEL=your-model-id
```

Choose a model available to your API project that supports Responses API structured outputs. Restart the API. Calls may incur usage charges. Keys stay on the backend; never use a `NEXT_PUBLIC_` variable for a secret.

Without an API key, chat is a deliberate offline stub, not an offline language model. Goal storage, demo data, check-ins, and progress calculations still work. No key is provided or shared by the repository.

## Optional recurring notifications

In **Settings → Notifications**, choose routines, then save and allow notifications. Each selected routine can notify at **each scheduled occurrence** while the API remains running. Preferences apply to the device/browser where you save them. Completed or skipped occurrences are not sent; this is not a repeated-nag system for one missed task.

Push delivery also needs your own VAPID public/private key pair in the root `.env`:

```dotenv
LIFE_OS_VAPID_PUBLIC_KEY=
LIFE_OS_VAPID_PRIVATE_KEY=
LIFE_OS_VAPID_SUBJECT=mailto:you@example.com
```

The public key is shared with the browser; the private key must remain secret. A blank pair leaves push delivery disabled. Use your push provider's VAPID key-generation instructions and restart the API after configuring the keys.

Desktop localhost supports service workers in supported browsers. Phone push requires your own **HTTPS** origin; `127.0.0.1` on a phone refers to the phone, not your computer. On iPhone, install the HTTPS site as a Home Screen web app and enable notifications from that app. This repository does not provision a public URL, certificates, or a push service for you. Keep the backend running for reminders.

## Optional integrations

The backend includes Google Gmail/Calendar and Oura/WHOOP connector code. Each user must register their own OAuth application, configure callback URLs, and consent to the required scopes. Google dependencies are optional:

```bash
python -m pip install -e '.[google-calendar,google-gmail]'
life-os --help
```

Leave these unset for local demo use. There are no connected accounts, scheduled email-processing jobs, private profiles, or wearable tokens included. The UI may show an integration as unavailable until you configure it.

## Local privacy and access

- Data is stored in `private/` and local SQLite/attachment files, not in GitHub.
- API keys and OAuth tokens belong in ignored local files or your own secret manager.
- With live AI or integrations enabled, the relevant content is sent to the configured provider. “Local” does not mean those optional API calls stay on your computer.
- This is a **single-user local application**, not an authenticated multi-user hosting service. A tenant ID is a data namespace, not an authentication boundary.
- Do not expose ports 3000 or 8000 to the internet without adding an authenticated access layer. The web proxy can add the API token; an API token alone does not authenticate users of the web app.
- To set an API token locally, put the same randomly generated `LIFE_OS_API_TOKEN` in root `.env` and `mobile/.env.local`, then restart both servers. `/health` remains public; `/docs` is a schema UI, not a login page. Supply `Authorization: Bearer <your-token>` for protected API requests.
- To reset local data, stop both servers and remove your configured SQLite database and its attachments. Back up anything you want to keep first.

## Build and test

```bash
# Repository root, virtual environment active
python -m pytest -q
python scripts/check_public_tree.py

# Web app
cd mobile
pnpm typecheck
pnpm build
pnpm start
```

The web production server also binds to `127.0.0.1:3000` by default. Build and runtime require your own local environment values; no cloud-specific build tooling is needed.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| “Local API is not responding” | Start `life-os serve` from the repository root; check `/health`; confirm `mobile/.env.local` points to port 8000. |
| Empty Plan | Seed the demo, choose today's date, or create and approve a goal plus its tracking protocol. |
| Chat asks for an API key | Expected without live AI configuration. Set both `OPENAI_API_KEY` and `LIFE_OS_MODEL`, then restart the backend. |
| 401 / unauthorized | Root and web `LIFE_OS_API_TOKEN` must match. Restart both processes after changing them. |
| Port already in use | Stop the previous process, or change `life-os serve --port 8001` and update `LIFE_OS_API_URL`. |
| No push notifications | Configure VAPID keys, allow device permission, select routines, and keep the API running. Phone access needs HTTPS. |
| Wrong reminder time | Set the goal's IANA timezone. Demo goals use `LIFE_OS_TIMEZONE`, defaulting to UTC. |
| `pnpm` or Python not found | Install the prerequisites above and reopen your terminal. |

## Contributing and security

Run the tests and public-tree check before submitting a change. Do not commit real profiles, screenshots of personal data, databases, tokens, or `.env` files. See [SECURITY.md](SECURITY.md) for the release's privacy boundary and reporting guidance.

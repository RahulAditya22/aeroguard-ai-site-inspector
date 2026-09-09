# AeroGuard AI

AI-assisted aerial site inspection and automated incident response.

AeroGuard accepts aerial/site images, sends them to a multimodal Gemini model, validates the response against a strict schema, classifies the inspection result, and records actionable incidents locally. It now includes both a CLI and a deployable Flask web dashboard.

## System architecture

```text
                    ┌───────────────┐
                    │ Aerial image  │
                    └───────┬───────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
          CLI command                 Web dashboard
              │                           │
              └─────────────┬─────────────┘
                            v
                  Image validation
                            │
                            v
                  Gemini multimodal API
                            │
                            v
                 Strict Pydantic schema
                            │
                            v
                   Deterministic triage
                       │          │
              ┌────────┘          └────────┐
              v                             v
        CSV + JSON records            Optional webhook
```

The web application keeps the Gemini API key server-side. Browser clients upload images to Flask; Flask calls Gemini with its configured environment variable and returns only the inspection result to the browser.

## Web dashboard

The dashboard provides:

- Drag-and-drop image upload with preview
- AI inspection with loading and error states
- Threat, severity, confidence, and automated-action indicators
- Description, recommended action, observations, and uncertainties
- Recent inspection history backed by the same CSV incident log
- Health endpoint for deployment monitoring
- Responsive layout for desktop and mobile screens

Run it locally:

```powershell
python -m aeroguard.web
```

Then open `http://localhost:5000`.

The browser never needs a Gemini API key.

## What it does

1. Validates image type, size, dimensions, and file integrity.
2. Sends the image to a multimodal Gemini model.
3. Requests structured JSON and validates it with Pydantic.
4. Applies deterministic severity-based routing in Python.
5. Writes an incident row to CSV and a detailed JSON report.
6. Optionally sends a webhook for configured high-severity incidents.

The system deliberately describes **AI-assisted inspection**, not guaranteed proof of a security violation. The model is instructed to report uncertainty instead of inventing facts.

## Recommended model

The default model is **Gemini 3.8 Flash** (`gemini-3.8-flash`). If your Google AI Studio account does not expose that model, set `GEMINI_MODEL` in `.env` or the deployment environment to another available multimodal Gemini model.

## API key setup

For local development:

1. Create a Gemini API key in Google AI Studio.
2. Copy `.env.example` to `.env`.
3. Put the key in `.env`:

```text
GEMINI_API_KEY=PASTE_YOUR_KEY_HERE
```

Do not commit `.env`. It is ignored by Git.

For Render, set `GEMINI_API_KEY` as a **secret environment variable** in the service settings. Do not put the production key in the repository.

## Installation

Python 3.11+ is required.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[test]"
Copy-Item .env.example .env
```

Edit `.env`, then use either interface:

```powershell
python -m aeroguard.cli inspect path\to\aerial_image.jpg
python -m aeroguard.web
```

### macOS/Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[test]'
cp .env.example .env
python -m aeroguard.cli inspect path/to/aerial_image.jpg
```

## Batch inspection

Inspect every supported image in a folder:

```powershell
python -m aeroguard.cli batch data\site_images
```

Results are written to `data/incidents.csv` and `reports/`.

## Web API

The Flask service exposes:

- `GET /` — dashboard
- `GET /api/health` — health check
- `GET /api/incidents` — recent incident records
- `POST /api/inspect` — multipart image inspection (`image` field)

The backend enforces the configured upload limit and accepted image extensions before invoking the inspection pipeline.

## Optional webhook alerts

Set these in `.env` or the deployment environment if you want high-severity incidents to trigger a webhook:

```text
ALERT_WEBHOOK_URL=
ALERT_MIN_SEVERITY=high
```

AeroGuard does not require a webhook to operate.

## Deploy to Render

The repository includes `render.yaml` for a Python web service. The service uses Gunicorn and binds to Render's `$PORT`.

After creating the Render service from this repository, configure the secret:

```text
GEMINI_API_KEY=<your private Gemini API key>
```

Render then builds and starts the Flask application. Because the key exists only in the server environment, users visiting the deployed site do not need their own Gemini key.

## Testing

The test suite does not call Gemini and therefore does not require an API key:

```powershell
pytest -q
```

Tests cover structured assessment validation, image validation, severity/action routing, CSV logging, webhook behavior, pipeline behavior with a mocked vision service, and the Flask web API.

GitHub Actions runs the test suite on pushes and pull requests to `main`.

## Project structure

```text
AeroGuard-AI/
├── .env.example
├── .github/
│   └── workflows/ci.yml
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml
├── render.yaml
├── requirements.txt
├── data/
│   └── .gitkeep
├── reports/
│   └── .gitkeep
├── src/
│   └── aeroguard/
│       ├── __init__.py
│       ├── actions.py
│       ├── cli.py
│       ├── config.py
│       ├── image_utils.py
│       ├── models.py
│       ├── pipeline.py
│       ├── vision.py
│       ├── web.py
│       ├── static/
│       │   ├── app.js
│       │   └── style.css
│       └── templates/
│           └── index.html
└── tests/
    ├── test_actions.py
    ├── test_image_utils.py
    ├── test_models.py
    ├── test_pipeline.py
    └── test_web.py
```

## Engineering choices

- **Multimodal inference:** uses Gemini for visual understanding instead of pretending a small custom model is accurate enough for general aerial scenes.
- **Structured output:** Pydantic validation prevents downstream code from trusting arbitrary model prose.
- **Separation of concerns:** image handling, AI inference, validation, action routing, persistence, CLI, and web presentation remain separate.
- **Safe credential handling:** secrets are read from environment variables and are never sent to the browser.
- **Safe failure:** missing credentials, invalid images, malformed model output, and webhook failures produce explicit errors rather than silent success.
- **Deterministic automation:** severity thresholds are implemented in Python, not left entirely to the model.
- **Deployable interface:** Flask and Gunicorn provide a lightweight production path without requiring a separate JavaScript build system.

## Data sources

Use aerial/site images that you are permitted to use. VisDrone is a useful public research dataset for aerial object detection, but not every image in a dataset will contain a security incident. For a meaningful demo, select a small test set containing people, vehicles, structures, and visibly abnormal/hazardous situations where possible.

## Limitations

AeroGuard is an AI-assisted inspection prototype. It is not a certified safety system, an identity-recognition system, or a substitute for trained human review. The model can miss small objects, misunderstand context, or misclassify ambiguous scenes. Production deployment would require a site-specific validation set, measured precision/recall, human escalation rules, monitoring, privacy controls, rate limiting, and a stronger deterministic vision layer where safety requirements demand it.

## Resume description

**AeroGuard AI — AI-Assisted Aerial Site Inspection & Incident Response**

Built and deployed a Python/Flask inspection platform that analyzes aerial imagery with a multimodal Gemini model, enforces structured Pydantic outputs, applies deterministic severity-based response rules, persists incidents to CSV/JSON, supports webhook alerts, exposes a secure web API, and includes automated CI tests for the decision pipeline and web layer.

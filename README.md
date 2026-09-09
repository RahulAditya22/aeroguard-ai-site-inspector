# AeroGuard AI

AI-assisted aerial site inspection and automated incident response.

AeroGuard accepts aerial/site images, sends them to a multimodal Gemini model, validates the response against a strict schema, classifies the inspection result, and records actionable incidents locally. It is designed as a small but complete engineering system rather than a one-off vision API demo.

## What it does

```text
Aerial image
    |
    v
Image validation + metadata
    |
    v
Gemini multimodal inspection
    |
    v
Strict Pydantic JSON schema
    |
    v
Threat/incident triage
    |
    +----> CSV incident log
    +----> JSON inspection record
    +----> Optional webhook alert
```

### Example decision

```json
{
  "threat_detected": true,
  "threat_type": "person_in_restricted_zone",
  "severity": "high",
  "confidence": 0.91,
  "description": "A person appears to be inside a visibly marked restricted area.",
  "recommended_action": "Alert site security and review the image.",
  "observations": ["person", "restricted boundary"],
  "uncertainties": []
}
```

The system deliberately describes **AI-assisted inspection**, not guaranteed proof of a security violation. The model is instructed to report uncertainty instead of inventing facts.

## Recommended model

The default model is **Gemini 3.8 Flash** (`gemini-3.8-flash`). Google's current documentation lists it as a multimodal Flash model with free-tier input/output pricing and support for visual workloads; free-tier rate limits still apply.

If your Google AI Studio account does not expose that model, change `GEMINI_MODEL` in `.env` to another available multimodal free-tier model.

## API key setup

1. Create a Gemini API key in Google AI Studio.
2. Copy `.env.example` to `.env`.
3. Put your key on **line 2** of `.env`:

```text
GEMINI_API_KEY=PASTE_YOUR_KEY_HERE
```

Do not commit `.env`. It is ignored by Git.

## Installation

Python 3.11+ is recommended.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env`, then run:

```powershell
python -m aeroguard.cli inspect path\to\aerial_image.jpg
```

### macOS/Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python -m aeroguard.cli inspect path/to/aerial_image.jpg
```

If running directly from the repository root, install the package with `pip install -e .`.

## Batch inspection

Inspect every supported image in a folder:

```powershell
python -m aeroguard.cli batch data\site_images
```

Results are written to `data/incidents.csv` and `reports/`.

## Optional webhook alerts

Set these in `.env` if you want high-severity incidents to trigger a webhook:

```text
ALERT_WEBHOOK_URL=
ALERT_MIN_SEVERITY=high
```

AeroGuard does not require a webhook to operate.

## Testing

The test suite does not call Gemini and therefore does not require an API key:

```powershell
pytest -q
```

The tests cover structured assessment validation, image validation, severity/action routing, CSV logging, disabled-webhook behavior, and end-to-end pipeline behavior with a mocked vision service.

GitHub Actions runs the same test suite on pushes and pull requests to `main`.

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
│       └── vision.py
└── tests/
    ├── test_actions.py
    ├── test_image_utils.py
    ├── test_models.py
    └── test_pipeline.py
```

## Engineering choices

- **Multimodal inference:** uses Gemini for visual understanding instead of pretending a small custom model is accurate enough for general aerial scenes.
- **Structured output:** Pydantic validation prevents downstream code from trusting arbitrary model prose.
- **Separation of concerns:** image handling, AI inference, validation, action routing, persistence, and CLI are separate modules.
- **Safe failure:** missing credentials, invalid images, malformed model output, and webhook failures produce explicit errors rather than silent success.
- **No API key in source:** secrets are read from environment variables.
- **Deterministic automation:** severity thresholds are implemented in Python, not left entirely to the model.

## Data sources

Use aerial/site images that you are permitted to use. VisDrone is a useful public research dataset for aerial object detection, but not every image in a dataset will contain a security incident. For a meaningful demo, select a small test set containing people, vehicles, structures, and visibly abnormal/hazardous situations where possible.

## Limitations

AeroGuard is an AI-assisted inspection prototype. It is not a certified safety system, an identity-recognition system, or a substitute for trained human review. The model can miss small objects, misunderstand context, or misclassify ambiguous scenes. Production deployment would require a site-specific validation set, measured precision/recall, human escalation rules, monitoring, privacy controls, and a stronger deterministic vision layer where safety requirements demand it.

## Resume description

**AeroGuard AI — AI-Assisted Aerial Site Inspection & Incident Response**

Built a Python inspection pipeline that analyzes aerial imagery with a multimodal Gemini model, enforces structured Pydantic outputs, applies deterministic severity-based response rules, persists incidents to CSV/JSON, supports webhook alerts, and includes automated tests for the complete offline decision pipeline.

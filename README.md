<div align="center">

# AI Resume Analyser

**Upload your resume. Get AI-powered career insights. Download your report.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Soubhagyakulkarni/Resume_Analyser)
[![Tests](https://img.shields.io/badge/Tests-pytest-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

### [Live App](https://resumeanalyser-mrxhennyfuc9femfqvernz.streamlit.app/)

</div>

---

## What Is This?

Streamlit application for evidence-grounded resume analysis, skill identification,
job recommendations from a Supabase PostgreSQL catalog, and downloadable PDF reports.
The system provides career-development support; it does not make hiring decisions.

---

## Requirements

- Python 3.11 or newer
- An API key for the selected AI provider (OpenAI or Gemini)

---

## How to Run Locally

### Step 1 — Clone the repository

```bash
git clone https://github.com/Soubhagyakulkarni/Resume_Analyser.git
cd Resume_Analyser
```

### Step 2 — Create a virtual environment

```powershell
# Windows (PowerShell)
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Create and configure Supabase

Create a project at [supabase.com](https://supabase.com/dashboard). Open **SQL Editor**
and run the complete script in
[`repositories/migrations/003_supabase_job_catalog.sql`](./repositories/migrations/003_supabase_job_catalog.sql).
This creates the jobs catalog and a restricted catalog refresh function. The app uses
Supabase Auth user metadata for display name and username; no password or extra profile
table is stored by the app. New users must confirm their email using the link Supabase
or a 6-digit code before they can sign in with their email and password. Phone numbers
and SMS are not required. To use the in-app code form, enable email confirmations and
update **Authentication → Email Templates → Confirm signup** to include `{{ .Token }}`
in the message body. Supabase's default confirmation link template will not provide a
code for that form. Set the Supabase Auth **Site URL** to your app URL and allow that
URL in its redirect settings.

The Supabase integration is being prepared locally and is not deployed to the linked live
app yet. The app will not start with the new code until the project migration and secrets
below are in place.

Copy the project URL, anon/publishable key, and service-role/secret key from **Project
Settings → API**. The service-role key bypasses row-level security: keep it only in the
server environment and never expose it in browser code or commit it.

### Step 5 — Set up your environment secrets

```powershell
# Windows
Copy-Item .env.example .env
```

```bash
# macOS / Linux
cp .env.example .env
```

Open `.env` and fill in your keys:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
ADZUNA_COUNTRY_CODE=in
```

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com/app/apikey).  
Get free Adzuna credentials at [developer.adzuna.com](https://developer.adzuna.com/signup).  
Never commit your `.env` file — it is already in `.gitignore`.

If you have the old local job catalog, migrate its active listings once after
the Supabase SQL migration and `.env` setup, but before the first app startup:

```powershell
python scripts\migrate_sqlite_jobs_to_supabase.py
```

The importer reads `data/jobs.sqlite3` in read-only mode, refuses an empty catalog,
and replaces the Supabase job catalog atomically. It does not import user accounts.
After this one-time import, the app uses PostgreSQL only.

For Gemini, set `AI_PROVIDER=gemini` and `GEMINI_API_KEY` in the ignored `.env` file.
For OpenAI, set `AI_PROVIDER=openai` and `OPENAI_API_KEY`. The selected provider and
key must match; a Gemini key cannot authenticate to OpenAI and vice versa. Never put
a real key in `.env.example`, commit `.env`, or place secrets in `.streamlit/config.toml`.

### Step 6 — Run the app

```powershell
# Windows
.\.venv\Scripts\streamlit.exe run app\main.py
```

```bash
# macOS / Linux
streamlit run app/main.py
```

The app will open at [http://localhost:8501](http://localhost:8501).

After changing `.env`, stop and restart Streamlit so the new configuration is loaded.
If the selected provider rejects the configured key, verify that it is active and
matches `AI_PROVIDER`; an API key that is syntactically present may still be
expired, revoked, or invalid for the configured provider account.

---

## Deploying to Streamlit Cloud (Free)

1. Push this repo to your GitHub account.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Select your repo → Branch: `main` → Main file: `app/main.py`.
4. Click **Deploy** — wait about 2 minutes.
5. Go to **Settings → Secrets** and paste:

```toml
AI_PROVIDER = "gemini"
GEMINI_API_KEY = "your_actual_key_here"
GEMINI_MODEL = "gemini-2.0-flash"
SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_ANON_KEY = "your_supabase_anon_key"
SUPABASE_SERVICE_ROLE_KEY = "your_supabase_service_role_key"

ADZUNA_APP_ID = "your_app_id"
ADZUNA_APP_KEY = "your_app_key"
ADZUNA_COUNTRY_CODE = "in"
```

6. Click **Save** — the app reboots automatically. Run the Supabase SQL migration
   above and set the Supabase Auth Site URL/redirect allowlist to the deployed app URL.
   Ensure email confirmations are enabled and the deployed app URL is allowed in the
   Supabase Auth redirect settings.

Future updates: just `git push origin main` and Streamlit Cloud redeploys automatically.

---

## App Features

The application accepts pasted resume text or PDF/DOCX files and refuses to analyze
a resume without a key for the selected provider. Resume bytes and analysis results
are held transiently for the active Streamlit session; the app does not persist them.
Resume text is sent to the configured AI provider only after the user accepts the
processing notice. Review provider data-processing terms and applicable privacy
requirements before deployment.

The landing page includes a synthetic sample resume for demonstration. Loading it
only fills the paste-text field; it does not submit or analyze anything. The same
explicit consent is required before any resume text — synthetic or user provided —
is sent to the configured provider. Consent is requested again for each new analysis attempt.

Career stage, primary goal, preferred role, and preferred location are optional.
They are held in the active Streamlit session only, can be skipped, and are not
stored in the database. Role/location preferences also filter recommendations.

The **Resume builder** workspace lets users create a resume from guided fields or
edit text extracted locally from an existing PDF/DOCX (pasted text is also
supported). The guided builder separates profile, experience/projects, and
education/skills, provides a transparent completeness checklist, and offers
Classic, Modern, and Compact PDF layouts with a live preview. The checklist is
not an ATS score. Use the **Review & export** step to see the finished resume
and select **Download PDF**. The generated order is Profile, Experience,
Projects, Education, Skills, then Certifications or activities. This workspace
does not call an AI provider or save resume content to PostgreSQL; users should
include only accurate information.

---

## Job Catalog

The job catalog is automatically populated from Adzuna and a curated seed catalog
on every app startup — no manual import is needed when running on Streamlit Cloud.

To refresh the catalog manually from Adzuna, [register for an Adzuna developer account](https://developer.adzuna.com/signup)
to obtain an `app_id` and `app_key`, place the resulting `ADZUNA_APP_ID` and
`ADZUNA_APP_KEY` in the ignored `.env` file, then run:

```powershell
python scripts\refresh_adzuna_catalog.py --what "graduate jobs" --where "India" --pages 3
```

The refresh defaults to the India country endpoint (`ADZUNA_COUNTRY_CODE=in`).
Only set the Adzuna credentials in `.env`; never paste them into chat, source
code, or logs. A failed or empty API response does not erase the existing
catalog.

Recommendations include only listings posted within the last 30 days by default.
Configure `JOB_LISTING_MAX_AGE_DAYS` in `.env` to a value from 1 to 365; older or
future-dated listings are excluded.

On the results page, optional target-role and preferred-location filters narrow both
matched recommendations and browse-only current listings. Separate role keywords with
commas (any keyword may match the job title); location is matched against the listing's
location. Leaving either field blank does not filter by it. Use **Apply job filters**
to update the list; this does not rerun AI analysis.

Results also include a role-linked skill-development plan. Skills are prioritized by
how often they appear in the filtered current listings, with curated links for a
limited set of skills. A skill not found in the resume is not proof that the user lacks it.

---

## Tests

```bash
pytest
```

Tests use synthetic content, temporary test databases, and fake AI dependencies;
they make no paid API calls.

---

## Analysis Output

The analysis includes a resume summary, evidence-backed technical and soft skills,
an experience assessment, job recommendations from the authorized catalog, skills
not found in the resume for those roles, learning suggestions, and resume
improvements. It also includes a role-linked skill development plan and transparent
ATS-friendly resume checks. Missing skills are phrased as *not found in the submitted
resume* and are not claims about what the person can or cannot do.

---

## Operational Notes

- The supported resume formats are PDF and DOCX (maximum 100 pages); scanned/image-only PDFs may not contain extractable text and are rejected.
- Configure provider, model, upload limits, timeouts, job-listing freshness, database location, and logging with the variables in `.env.example`.
- `requirements.txt` contains the production dependencies.
- See [PRD.md](PRD.md), [SOFTWARE_ARCH.md](SOFTWARE_ARCH.md), and [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for product and architecture details.

---

## Privacy & Security

- Resume text is sent to Gemini only after explicit user consent.
- No resume content is stored in the database — session only.
- Passwords are securely hashed; never stored as plaintext.
- API keys are read from environment / Streamlit Secrets — never hardcoded.
- All job application URLs validated as real HTTPS links.

---

<div align="center">

Built by **Soubhagya Kulkarni**

[![GitHub](https://img.shields.io/badge/GitHub-Soubhagyakulkarni-181717?style=flat-square&logo=github)](https://github.com/Soubhagyakulkarni)

</div>

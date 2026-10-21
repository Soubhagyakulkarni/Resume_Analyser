# AI Resume Analyzer

Streamlit application for evidence-grounded resume analysis, skill identification,
job recommendations from an authorized SQLite catalog, and downloadable PDF reports.
The system provides career-development support; it does not make hiring decisions.

## Requirements

- Python 3.11 or newer
- An API key for the selected AI provider (OpenAI or Gemini)
- An authorized job-catalog CSV for job recommendations

## Setup

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

For Gemini, set `AI_PROVIDER=gemini` and `GEMINI_API_KEY` in the ignored `.env`
file. For OpenAI, set `AI_PROVIDER=openai` and `OPENAI_API_KEY`. The selected
provider and key must match; a Gemini key cannot authenticate to OpenAI and vice
versa. Never put a real key in `.env.example`, commit `.env`, or place secrets in
`.streamlit/config.toml`.

## Run

```powershell
.\.venv\Scripts\python.exe -m streamlit run app\main.py
```

After changing `.env`, stop and restart Streamlit so the new configuration is loaded.
If the selected provider rejects the configured key, verify that it is active and
matches `AI_PROVIDER`; an API key that is syntactically present may still be
expired, revoked, or invalid for the configured provider account.

The application accepts pasted resume text or PDF/DOCX files and refuses to analyze
a resume without a key for the selected provider. Resume bytes and analysis
results are held transiently for the active Streamlit session; the app does not
persist them. Resume text is sent to the configured AI provider only after the
user accepts the processing notice. Review provider data-processing
terms and applicable privacy requirements before deployment.

The landing page includes a synthetic sample resume for demonstration. Loading
it only fills the paste-text field; it does not submit or analyze anything. The
same explicit consent is required before any resume text—synthetic or user
provided—is sent to the configured provider. Consent is requested again for
each new analysis attempt.

Career stage, primary goal, preferred role, and preferred location are optional.
They are held in the active Streamlit session only, can be skipped, and are not
stored in SQLite. Role/location preferences also filter recommendations.

The **Resume builder** workspace lets users create a resume from guided fields or
edit text extracted locally from an existing PDF/DOCX (pasted text is also
supported). The guided builder separates profile, experience/projects, and
education/skills, provides a transparent completeness checklist, and offers
Classic, Modern, and Compact PDF layouts with a live preview. The checklist is
not an ATS score. Use the **Review & export** step to see the finished resume
and select **Download PDF**. The generated order is Profile, Experience,
Projects, Education, Skills, then Certifications or activities. This workspace
does not call an AI provider or save resume content to SQLite; users should
include only accurate information.

## Job catalog

Populate the catalog only with data from an authorized source. CSV columns:

`id,title,description,required_skills,location,application_url,source,updated_at`

Separate required skills with `|`; use ISO dates (`YYYY-MM-DD`) and HTTPS
application links. Import with:

```powershell
python scripts\refresh_job_catalog.py path\to\authorized_jobs.csv
```

The CSV import validates the input and atomically replaces the SQLite catalog.
To refresh it directly from Adzuna, [register for an Adzuna developer account](https://developer.adzuna.com/signup)
to obtain an `app_id` and `app_key`,
place the resulting `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` in the ignored `.env`
file, then run:

```powershell
python scripts\refresh_adzuna_catalog.py --what "graduate jobs" --where "India" --pages 3
```

The refresh defaults to the India country endpoint (`ADZUNA_COUNTRY_CODE=in`).
Only set the Adzuna credentials in `.env`; never paste them into chat, source
code, or logs. A failed or empty API response does not erase the existing
catalog. Imported descriptions are used to identify a limited set of
explicitly-mentioned skills; unsupported skills are not inferred into listing
requirements.

Recommendations include only listings posted within the last 30 days by
default. Configure `JOB_LISTING_MAX_AGE_DAYS` in `.env` to a value from 1 to
365; older or future-dated listings are excluded. Results explain when listings
are missing or excluded as stale. Verify Adzuna's current API terms, display
requirements, geographic coverage, and account quotas before production use.

On the results page, optional target-role and preferred-location filters narrow
both matched recommendations and browse-only current listings. Separate role
keywords with commas (any keyword may match the job title); location is matched
against the listing's location. Leaving either field blank does not filter by it.
Use **Apply job filters** to update the list; this does not rerun AI analysis.
Preferences stay in the current Streamlit session and are not added to the job
catalog or persisted as a profile. Work-arrangement filtering is not offered
because the current catalog integration does not provide a consistently
verified work-arrangement field.

Results also include a role-linked skill-development plan. Skills are prioritized
by how often they appear in the filtered current listings, with curated links for
a limited set of skills; other skills receive a practical project suggestion
without an invented resource link. A skill not found in the resume is not proof
that the user lacks it.

The results page presents a career snapshot and next actions followed by tabs for
resume insights, job recommendations, the skill plan, resume quality checks, and
the PDF report. Student/fresher profiles receive an optional projects/practical
work reminder. Job cards show the listing source, location, listing date, and
available description; the current job model does not include a verified company
name, so the UI does not invent one. Matched listings can be sorted by relevance,
newest, or location.

The Resume Quality Checks are deterministic reminders about extracted-text
readability, conventional section headings, measurable outcomes, and skill terms
found in filtered current listings. Student/fresher profiles also see an optional
projects check. They are not an ATS score and cannot predict
an employer's screening result. The filtered skill plan and checks are included
in the downloadable PDF report. Extracted resume text is kept only in the active
Streamlit session to compare it with changed job filters, is not persisted to the
catalog or database, and is cleared when a new analysis starts or the session ends.
The repository contains no active fabricated production listings. Its synthetic
sample catalog is kept under `tests/fixtures/` and the importer rejects its
placeholder application domains. Do not import demo data as live opportunities.

## Tests

```powershell
python -m pytest
```

Tests use synthetic content, temporary SQLite databases, and fake AI dependencies;
they make no paid API calls.

## Analysis output

The analysis includes a resume summary, evidence-backed technical and soft skills,
an experience assessment, job recommendations from the authorized catalog, skills
not found in the resume for those roles, learning suggestions, and resume
improvements. It also includes a role-linked skill development plan and transparent
ATS-friendly resume checks. Missing skills are phrased as not found in the submitted
resume and are not claims about what the person can or cannot do.

## Operational notes

- The supported resume formats are PDF and DOCX (maximum 100 pages); scanned/image-only PDFs may not
  contain extractable text and are rejected. DOCX archives are also bounded after decompression.
- Configure provider, model, upload limits, timeouts, job-listing freshness, database location, and
  logging with the variables in `.env.example`, including the maximum analysis text length.
- `requirements.lock` is a fully resolved Python 3.13 lock. Re-resolve it for the
  target platform/runtime when deployment requirements differ.
- See [PRD.md](PRD.md), [SOFTWARE_ARCH.md](SOFTWARE_ARCH.md), and
  [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for product and architecture details.

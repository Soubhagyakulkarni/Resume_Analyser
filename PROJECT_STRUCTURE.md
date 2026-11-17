# Python Project Structure

## AI Resume Analyzer

| Document detail | Value |
|---|---|
| Status | Proposed |
| Version | 1.0 |
| Last updated | 2026-10-05 |
| Product requirements | [PRD.md](./PRD.md) |
| Architecture | [SOFTWARE_ARCH.md](./SOFTWARE_ARCH.md) |
| Runtime stack | Streamlit, Python, OpenAI GPT, SQLite |
| Test stack | pytest |

## 1. Design Principles

- **Modularity:** Separate Streamlit presentation, application workflows, domain models, and external adapters.
- **Testability:** Keep business rules independent of Streamlit, OpenAI, and live SQLite data; inject interfaces and use test doubles.
- **Maintainability:** Give each module one clear responsibility, validate data at boundaries, and keep configuration out of business logic.
- **Scalability:** Begin as a modular monolith; isolate SQLite and AI behind replaceable adapters. Keep user resumes/results transient by default as specified in the architecture.
- **Privacy:** Use synthetic test data, do not log resume content, and do not commit secrets, real resumes, reports, or production database files.

This document describes the implemented scaffold and its intended module boundaries.

The implemented analysis response includes a summary, technical and soft skills,
experience assessment, evidence-grounded job recommendations, skills not found in
the submitted resume for recommended roles, learning suggestions, and resume
improvements. Users may paste resume text or upload PDF/DOCX.

## 2. Folder Structure

```text
resume-analyzer/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── resume_service.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── resume_prompt.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── errors.py
│   │   ├── identifiers.py
│   │   ├── text_safety.py
│   │   └── logging_config.py
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── analyze_resume.py
│   │   ├── results.py
│   │   └── resume_builder.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── upload_form.py
│   │   ├── analysis_view.py
│   │   └── status_messages.py
│   └── session_state.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── logging_config.py
├── integrations/
│   ├── __init__.py
│   ├── gemini_gateway.py
│   └── openai_gateway.py
├── models/
│   ├── __init__.py
│   ├── resume.py
│   ├── analysis.py
│   └── job.py
├── parsers/
│   ├── __init__.py
│   ├── file_validator.py
│   ├── pdf_parser.py
│   └── docx_parser.py
├── prompts/
│   ├── __init__.py
│   ├── resume_analysis.txt
│   └── prompt_loader.py
├── reports/
│   ├── __init__.py
│   ├── pdf_renderer.py
│   └── resume_pdf_renderer.py
├── repositories/
│   ├── __init__.py
│   ├── sqlite_job_repository.py
│   └── migrations/
│       └── 001_create_job_catalog.sql
├── services/
│   ├── __init__.py
│   ├── ports.py
│   ├── resume_service.py
│   ├── analysis_service.py
│   ├── recommendation_service.py
│   ├── resume_builder_service.py
│   └── report_service.py
├── utils/
│   ├── __init__.py
│   ├── errors.py
│   ├── identifiers.py
│   └── text_safety.py
├── scripts/
│   └── refresh_job_catalog.py
├── data/
│   └── .gitkeep
├── tests/
│   ├── conftest.py
│   ├── fixtures/
│   │   ├── sample_resume.pdf
│   │   ├── sample_resume.docx
│   │   ├── sample_analysis.json
│   │   └── sample_jobs.csv
│   ├── unit/
│   │   ├── test_file_validator.py
│   │   ├── test_analysis_service.py
│   │   └── test_recommendation_service.py
│   ├── integration/
│   │   ├── test_sqlite_job_repository.py
│   │   └── test_analysis_workflow.py
│   ├── contract/
│   │   └── test_openai_gateway.py
│   └── ui/
│       └── test_streamlit_workflow.py
├── .streamlit/
│   └── config.toml
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.lock
└── README.md
```

All resume fixtures must be synthetic and non-identifying. `data/` is for a runtime job catalog only; production databases and any user data must be excluded from version control.

## 3. File Names, Purpose, and Responsibilities

### `app/` — Streamlit entry point and presentation

| File | Purpose and responsibilities |
|---|---|
| `app/main.py` | Streamlit entry point. Initializes configuration, logging, adapters, and services; configures page layout and navigation. Contains no analysis or matching rules. |
| `app/pages/analyze_resume.py` | Renders the submission workflow, privacy notice, supported-format guidance, user preferences, and processing status. Calls the resume/analysis service interface. |
| `app/pages/results.py` | Renders validated analysis, evidence, recommendations, skill gaps, improvement suggestions, and report download action. Shows partial failures clearly. |
| `app/pages/resume_builder.py` | Renders the guided session-only resume builder, deterministic completeness review, existing-resume text editor, live preview, and PDF template selection/download. |
| `app/components/upload_form.py` | Reusable accessible upload controls and client-side guidance. Server-side validation remains authoritative. |
| `app/components/home_sections.py` | Landing-page hero-supporting content, sample resume loader, value cards, and process/limitations disclosure. |
| `app/components/career_profile.py` | Optional session-only career-profile controls; does not persist profile data. |
| `app/components/analysis_view.py` | Tabbed result sections with clear labels for extracted evidence, inference, recommendations, checks, and report download. |
| `app/components/career_snapshot.py` | Career snapshot metrics and deterministic next-action cards. |
| `app/components/job_cards.py` | Matched and browse-only job card presentation and sort ordering. |
| `app/components/skill_plan_view.py` | Prioritized skill-development tiers and generic weekly focus plan. |
| `app/components/quality_checks_view.py` | Transparent, non-scored resume quality-check presentation. |
| `app/components/footer.py` | Product tagline, version, career-guidance disclaimer, and privacy note. |
| `app/components/status_messages.py` | Maps typed application outcomes to safe, actionable Streamlit status messages; never renders stack traces or provider payloads. |
| `app/session_state.py` | Defines session keys, active workflow state, reset/cleanup behavior, and storage of only the transient data required by the current session. |
| `app/__init__.py`, `app/pages/__init__.py`, `app/components/__init__.py` | Mark Python packages; keep exports minimal and avoid import-time application side effects. |

### `config/` — runtime configuration

| File | Purpose and responsibilities |
|---|---|
| `app/config/settings.py` | Canonical settings loader and validator. Reads local `.env` for development and protected environment/secret injection in deployment; validates model, timeouts, upload/text bounds, database path, and log level. Contains no secret values. |
| `app/utils/logging_config.py` | Canonical logging setup, configured once at startup. Root `config/logging_config.py` is a compatibility import. |
| `app/utils/errors.py`, `app/utils/identifiers.py`, `app/utils/text_safety.py` | Canonical error types, opaque IDs, and evidence-safe text helpers, imported by the UI and service layer to avoid Streamlit path collisions. |
| `config/settings.py` | Compatibility import for `app.config.settings`, retained for existing architecture/import paths. |
| `config/__init__.py` | Package marker; imports have no startup side effects beyond settings module behavior. |

### `services/` — application workflows and ports

| File | Purpose and responsibilities |
|---|---|
| `services/ports.py` | Defines Python `Protocol` interfaces for AI analysis, job-catalog queries, parsing, and report rendering. These contracts are implemented by adapters and can be faked in tests. |
| `app/services/resume_service.py` | Canonical resume input service. Validates PDF/DOCX uploads or pasted text, enforces configured size bounds, and returns typed parsed-resume data. |
| `services/resume_service.py` | Compatibility import for the canonical application resume service. |
| `services/analysis_service.py` | Orchestrates AI-assisted skills/experience extraction and summary/suggestions; validates model output against models and evidence constraints before returning it. |
| `services/recommendation_service.py` | Retrieves current catalog records, applies documented deterministic matching, explains match evidence, and identifies skills not found in the resume. Never invents job records or asserts the user lacks an unmentioned skill. |
| `services/career_profile.py` | Defines optional career-profile types, evidence-derived readiness and next-action helpers, job-match strength labels, skill-tier grouping, and a synthetic demonstration resume. Pure deterministic helpers only. |
| `services/resume_quality_service.py` | Performs deterministic extracted-text, section-heading, measurable-outcome, listing-keyword, and contextual student/fresher project checks. Does not generate an ATS score. |
| `services/skill_development_service.py` | Prioritizes skills not evidenced in the resume across filtered current listings and resolves only curated HTTPS learning resources. |
| `services/report_service.py` | Assembles validated report data and invokes the renderer. Keeps report generation independent from the Streamlit page. |
| `services/resume_builder_service.py` | Converts user-entered draft fields into ordered resume sections and deterministic completeness suggestions without inventing content. |
| `reports/resume_pdf_renderer.py` | Renders user-authored resume content in Classic, Modern, or Compact PDF layouts without persistence. |
| `services/__init__.py` | Package marker; avoid service construction or external API calls during import. |

### `models/` — typed application and domain data

| File | Purpose and responsibilities |
|---|---|
| `models/resume.py` | Types for validated resume metadata and extracted text/evidence references. Does not represent persisted user resumes in the MVP. |
| `models/analysis.py` | Validated summary, technical/soft skills, experience assessment, learning suggestions, resume improvements, and caveats. Encodes distinctions between extracted and inferred information. |
| `models/job.py` | Job listing, source/freshness metadata, required skills, match explanation, and gap models. |
| `models/__init__.py` | Package marker; exports only stable model contracts if needed. |

### `parsers/` — upload validation and text extraction

| File | Purpose and responsibilities |
|---|---|
| `parsers/file_validator.py` | Checks file size, extension, content signature, and supported format; rejects empty or unsupported content before parsing or AI calls. |
| `parsers/pdf_parser.py` | Extracts text from supported PDFs; reports encrypted, corrupted, empty, and unextractable cases as typed errors. |
| `parsers/docx_parser.py` | Extracts text from supported DOCX files and reports malformed or empty documents as typed errors. |
| `parsers/__init__.py` | Package marker; parser registry/factory may be exposed here if there are multiple formats. |

### `integrations/` — external provider adapters

| File | Purpose and responsibilities |
|---|---|
| `integrations/openai_gateway.py` | Implements the AI port using the OpenAI SDK. Applies timeouts, bounded retries for transient errors, minimal data transfer, strict response parsing, and normalized provider error mapping. |
| `integrations/gemini_gateway.py` | Implements the same AI port using Google's Gemini SDK, requesting JSON and normalizing provider/authentication failures. |
| `integrations/__init__.py` | Package marker; provider clients are initialized only after configuration validation. |

### `prompts/` — versioned prompt assets

| File | Purpose and responsibilities |
|---|---|
| `prompts/resume_analysis.txt` | Static, reviewed instruction template for evidence-grounded analysis. Treats resume content as untrusted data, prohibits invented claims, and requests the agreed structured response. Contains no secrets or user data. |
| `app/prompts/resume_prompt.py` | Loads the reviewed static prompt without interpolating resume content. |
| `prompts/prompt_loader.py` | Compatibility loader for `app.prompts.resume_prompt`; the template asset remains `prompts/resume_analysis.txt`. |
| `prompts/__init__.py` | Package marker. |

### `repositories/` — persistence boundary

| File | Purpose and responsibilities |
|---|---|
| `repositories/sqlite_job_repository.py` | Implements catalog reads and controlled refresh writes with parameterized SQL, transaction boundaries, and freshness/source metadata. Does not store resumes or analysis results by default. |
| `repositories/migrations/001_create_job_catalog.sql` | Creates the initial normalized job/catalog-source schema. Migrations are ordered, repeatable under the migration runner, and contain no data secrets. |
| `repositories/__init__.py` | Package marker; exports repository factory only if needed. |

### `reports/` — output rendering

| File | Purpose and responsibilities |
|---|---|
| `reports/pdf_renderer.py` | Converts validated report models into an accessible, printable PDF. Escapes content, excludes internal diagnostics, and returns bytes for direct download without persistent storage by default. |
| `reports/__init__.py` | Package marker. |

### `utils/` — cross-cutting helpers

| File | Purpose and responsibilities |
|---|---|
| `utils/errors.py`, `utils/identifiers.py`, `utils/text_safety.py` | Compatibility imports for the canonical implementations in `app/utils/`. |
| `utils/__init__.py` | Package marker; avoid turning this into a catch-all location for business logic. |

### `tests/`, scripts, and root configuration

| File | Purpose and responsibilities |
|---|---|
| `tests/conftest.py` | Shared pytest fixtures: temporary SQLite databases, fake AI gateway, synthetic models, and deterministic settings. |
| `tests/fixtures/sample_resume.pdf`, `sample_resume.docx` | Synthetic, non-personal parser/UI fixtures only. |
| `tests/fixtures/sample_analysis.json`, `sample_jobs.csv` | Synthetic AI output and job catalog fixtures; never import sample listings as live vacancies. |
| `tests/unit/` | Fast isolated tests for validation, evidence rules, career profile framing, readiness, next actions, recommendation sorting, skill tiers, PDF assembly, and error mapping. |
| `tests/integration/` | Tests for SQLite repository, migrations, parser-to-service workflow, and report assembly using temporary resources. |
| `tests/contract/` | Tests for OpenAI and Gemini adapter request/response contracts and provider-error normalization using fakes/synthetic responses. |
| `tests/ui/` | Streamlit workflow tests for synthetic demo/consent, job filters, dashboard empty states, visible failures, results, and report download. |
| `scripts/refresh_job_catalog.py` | Explicitly invoked, authorized catalog import/refresh command with validation, provenance, and safe failure reporting. |
| `data/.gitkeep` | Keeps the runtime data directory in source control without including the actual database. |
| `.streamlit/config.toml` | Non-secret Streamlit presentation/runtime settings only. |
| `.env.example` | Documents variable names and safe placeholders; never include real keys. |
| `.gitignore` | Excludes virtual environments, caches, local environment files, databases, resumes, reports, logs, and build artifacts. |
| `pyproject.toml` | Project metadata, dependency declarations, pytest configuration, and formatter/linter/type-checker settings. |
| `requirements.lock` | Fully pinned deployment dependency set generated by the selected dependency workflow. |
| `README.md` | Local setup, supported inputs, test/run commands, configuration, data refresh, privacy, and operational notes. |

## 4. Responsibilities by Layer

1. **Presentation (`app/pages/`, `app/components/`):** Collect pasted text or uploaded input, display status/results, and initiate downloads. It may depend on application services but not on provider SDKs or SQL.
2. **Application orchestration (`services/`):** Implement user workflows, coordinate interfaces, enforce workflow sequencing, and return typed outcomes. It must not import Streamlit.
3. **Domain/boundary models (`models/`):** Define validated data contracts and domain invariants. Keep models independent of UI widgets and provider response classes.
4. **Infrastructure adapters (`integrations/`, `repositories/`, `parsers/`, `reports/`):** Implement external API, persistence, file, and rendering details behind service contracts.
5. **Cross-cutting (`config/`, `utils/`):** Supply validated configuration, logging, errors, and small infrastructure helpers. Keep domain decisions in domain/application modules.
6. **Tests (`tests/`):** Verify contracts and behavior without real resumes, secrets, external paid calls, or production databases.

## 5. Dependency Relationships

### Allowed dependency direction

```text
app/  ───────────► services/ ───────────► models/
                       ▲                    ▲
                       │                    │
config/ ─► app bootstrap│                    │
                       │                    │
integrations/ ─────────┘                    │
repositories/ ─────────────────────────────┤
parsers/ ──────────────────────────────────┤
reports/ ──────────────────────────────────┘
prompts/ ◄──────── integrations/ (prompt asset loading)
utils/   ◄──────── cross-cutting modules (narrow helpers only)
tests/   ─────────► all production modules (never the reverse)
```

### Dependency rules

- `app/` calls `services/` and renders returned models. It must not call OpenAI or execute SQL directly.
- `services/` depends on `models/` and abstract ports defined in `services/ports.py`. Concrete adapters are supplied during application startup through dependency injection.
- `integrations/`, `repositories/`, `parsers/`, and `reports/` implement contracts and may depend on `models/`, `config/`, and narrowly scoped `utils/`; they must not depend on Streamlit pages.
- `models/` must not import `app/`, `services/`, Streamlit, OpenAI SDK, or SQLite adapters.
- `config/` loads and validates settings but must not perform analysis, database queries, or network calls on import.
- `prompts/` contains static assets and loading logic only. Resume content is bound at runtime as untrusted input; prompts never import UI code or contain credentials.
- `utils/` must not import higher-level application modules. Avoid circular dependencies and generic helper modules that accumulate business rules.
- `tests/` can import any production layer and inject fakes, but production code must never import test modules.

### Main runtime dependency composition

At startup, `app/main.py` loads validated settings and configures logging, creates the SQLite job repository and OpenAI gateway, injects those adapters into application services, and exposes the services to Streamlit page handlers. Services receive protocols rather than concrete SDK/database clients. Unit tests construct services with fake protocol implementations; repository integration tests use a temporary SQLite database.

## 6. Modularity and Growth Path

- Keep the initial application a single deployable modular monolith; do not split services into networked microservices without measured need.
- Keep provider-specific calls within their integration gateway; changing provider should not require editing pages or recommendation rules.
- Keep job storage behind a repository contract. SQLite suits the initial, modest single-writer catalog; use the same contract to migrate to PostgreSQL if measured concurrency or availability needs exceed SQLite.
- If authentication, counselor sharing, or institution dashboards are added, introduce explicit identity, authorization, consent, and tenant boundaries before adding persistent resume/result records.
- Add new parsers, job sources, or report formats as adapters while retaining the existing service contracts.

## 7. Implementation Notes

- This is a proposed scaffold, not a claim that these files already exist. Create modules as features are implemented rather than filling the repository with empty files.
- Choose one canonical definition for each interface (service protocol or repository contract) and avoid duplicate abstractions.
- Keep generated files and user-provided uploads out of version control. Test data must be synthetic.
- Add targeted tests alongside each implementation slice; maintain CI gates for formatting/linting, type checking where configured, and pytest.

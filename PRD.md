# Product Requirements Document

## AI Resume Analyser & Job Recommendation System

| Field | Value |
|---|---|
| Status | **Live – v1.1** |
| Version | 1.1 |
| Last updated | 2026-10-21 |
| Related document | [SOFTWARE_ARCH.md](./SOFTWARE_ARCH.md) |
| AI provider | Google Gemini (`gemini-flash-latest`) |
| Runtime | Streamlit · Python 3.12 · SQLite |

---

## 1. Executive Summary

A Streamlit web application that lets students, job seekers, and career counselors upload or paste a resume, receive an AI-powered structured analysis, compare it against any job description, identify skill gaps, and download a formatted PDF report — all in a single session with no login required.

---

## 2. Problem Statement

Most resume feedback is either too generic (online templates) or too expensive (paid career coaches). Entry-level candidates waste hours tailoring resumes without knowing which keywords or skills actually matter for a specific role. The product gives instant, evidence-grounded feedback using the same large-language-model technology recruiters use, while making clear what is inferred versus explicitly stated in the resume.

---

## 3. Business Objectives

| # | Objective | Success metric |
|---|---|---|
| B1 | Reduce time to "actionable feedback" for a job seeker | Analysis + JD match in under 30 seconds |
| B2 | Make skill gaps visible, not vague | Missing keywords list derived directly from pasted JD |
| B3 | Build trust through transparency | Every suggestion labelled with a rule; no invented facts |
| B4 | Support recruiters and placement officers with demo-able output | Share-able PDF report, polished Plotly chart |

---

## 4. User Personas

### 4.1 The Fresh Graduate (primary)
- **Context:** Applying for first job; no HR network; unsure which skills to highlight.
- **Pain point:** Rejection emails with no reason given.
- **Goal:** Know *exactly* what is missing before clicking Submit.

### 4.2 The Career Switcher
- **Context:** 3–5 years in one domain; pivoting to adjacent role.
- **Pain point:** Resume written for the old role; doesn't map to new JD language.
- **Goal:** JD match score and targeted keyword list.

### 4.3 The Career Counselor / Placement Officer
- **Context:** Reviews 20+ resumes per week; needs a quick first screen.
- **Goal:** Upload a resume, download a PDF report to share with the student.

---

## 5. Functional Requirements

### 5.1 Resume Input — DONE

| ID | Requirement | Status |
|---|---|---|
| F1.1 | Accept PDF, DOCX, and TXT resume uploads up to 5 MB | Done |
| F1.2 | Accept pasted plain-text resume via text area | Done |
| F1.3 | Validate file signature (not just extension); reject encrypted/empty files | Done |
| F1.4 | Show explicit consent notice before sending text to AI provider | Done |
| F1.5 | Extract text from DOCX tables (not only paragraphs) | Done |
| F1.6 | Handle malformed PDFs with non-strict parsing and per-page recovery | Done |

### 5.2 Resume Analysis — DONE

| ID | Requirement | Status |
|---|---|---|
| F2.1 | Send resume text to Gemini and receive structured JSON analysis | Done |
| F2.2 | Extract: skills (technical + soft), experience years, education, career summary | Done |
| F2.3 | Label skills as evidenced vs inferred | Done |
| F2.4 | Validate all AI output against schema before displaying | Done |
| F2.5 | Show a Career Snapshot (level, top skills, experience) above the tabs | Done |

### 5.3 Job Recommendation Engine — DONE

| ID | Requirement | Status |
|---|---|---|
| F3.1 | Match resume skills against SQLite job catalog using deterministic scoring | Done |
| F3.2 | Show match %, missing skills, and job source metadata per listing | Done |
| F3.3 | Fetch live job listings from Adzuna API when catalog is stale | Done |
| F3.4 | A job must exist in the catalog to be recommended (no hallucinated listings) | Done |

### 5.4 JD Match and Skills Analyser — DONE (new in v1.1)

| ID | Requirement | Status |
|---|---|---|
| F4.1 | User pastes any job description; system extracts keywords deterministically | Done |
| F4.2 | Produce a match score (0-100) based on keyword overlap | Done |
| F4.3 | Show matched keywords (green) and missing keywords (red) as chips | Done |
| F4.4 | Before/after rewrite suggestions based on structural rules only — no metrics invented | Done |
| F4.5 | Skills bar chart (Plotly) showing evidenced vs inferred skills | Done |

### 5.5 Resume Quality Checks — DONE

| ID | Requirement | Status |
|---|---|---|
| F5.1 | Check for weak openers, vague quantifiers, filler phrases | Done |
| F5.2 | Each check shows the rule and a "not invented" caveat | Done |

### 5.6 Skill Development Plan — DONE

| ID | Requirement | Status |
|---|---|---|
| F6.1 | Show ordered learning steps to close the gap for a target role | Done |

### 5.7 Downloadable Report — DONE

| ID | Requirement | Status |
|---|---|---|
| F7.1 | Generate a PDF report from validated analysis data | Done |
| F7.2 | Report is generated in-memory; not stored server-side | Done |

---

## 6. Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NF1 | Analysis end-to-end latency | < 30 s on typical home broadband |
| NF2 | Upload size limit | 5 MB |
| NF3 | Resume text length limit | 15,000 chars |
| NF4 | JD text length limit | 15,000 chars |
| NF5 | No resume text stored server-side by default | Enforced in session state |
| NF6 | All tests pass offline with no real API keys | 175 / 175 |
| NF7 | Privacy: no PII in logs | Enforced in logging config |
| NF8 | Accessibility: keyboard-usable core UI | Streamlit defaults |

---

## 7. User Stories

| Story | Acceptance Criteria |
|---|---|
| As a graduate I want to upload my PDF and instantly see a skills gap | Upload then Analysis then Resume Insights tab shows skills with evidence labels |
| As a job seeker I want to paste a JD and get a match score | JD tab then score gauge then matched/missing keyword chips visible |
| As a user I want to see what bullets to fix before applying | JD tab then Before/After rewrite section with rule stated |
| As a counselor I want to download a report for my student | Download Report tab then one click then PDF bytes served |
| As a user I want to see a visual summary of my skills | JD tab then Plotly bar chart with evidenced vs inferred shading |

---

## 8. Out of Scope (MVP)

- User accounts / login
- Saving analysis history across sessions
- Counselor multi-student dashboard
- Automated job application
- Scanned/image-only PDF OCR (returns a clear error message)
- Mobile-native app

---

## 9. Known Risks

| Risk | Mitigation |
|---|---|
| Gemini API network drops (wsarecv) | Retry logic + timeout config; falls back to user-retryable error |
| Model alias changes (gemini-flash-latest is a moving pointer) | Pin to a versioned alias when Google stabilises naming |
| Keyword extractor misses domain-specific multi-word phrases | JD matcher uses phrase patterns + CamelCase detection; acceptable for MVP |
| SQLite write contention on multi-user deploy | Documented; upgrade to PostgreSQL before scaling |
| PDF with no extractable text (scanned image) | Detected via empty text after parsing; user shown clear message |

---

## 10. Roadmap / Future Enhancements

| Priority | Feature |
|---|---|
| High | Pin Gemini model to a specific versioned alias |
| High | AI-powered rewrite suggestions (single bullet improved via Gemini) |
| Medium | Radar chart (spider chart) for skills by category |
| Medium | Counselor mode: batch-upload + compare multiple resumes |
| Low | ATS simulation: predict which ATS systems will parse the resume correctly |
| Low | Cover letter generator tied to the JD pasted by the user |
| Low | User accounts and saved history (requires auth + privacy review) |

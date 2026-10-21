<div align="center">

# 🤖 AI Resume Analyser

**Upload your resume. Get AI-powered career insights. Download your report.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Soubhagyakulkarni/Resume_Analyser)
[![Tests](https://img.shields.io/badge/Tests-177%20Passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

### [🚀 Try the Live App →](https://your-app.streamlit.app)

*Replace the link above with your actual Streamlit Cloud URL*

</div>

---

## 📌 What Is This?

**AI Resume Analyser** is a full-stack AI-powered career tool that helps job seekers — especially **freshers and graduates** — understand their resume's strengths and gaps, discover matched job opportunities, and build a professional ATS-ready resume from scratch.

It uses **Google Gemini AI** to deeply analyse your resume text and generate evidence-backed career insights without fabricating information or making hiring decisions.

---

## ✨ Features At a Glance

| Feature | Description |
|---|---|
| 📄 **Resume Analysis** | Upload PDF/DOCX or paste text. Gemini AI extracts skills, experience signals, and career level |
| 🎯 **ATS Score & Insights** | Get a career snapshot with ATS alignment tips, improvement checklist, and actionable next steps |
| 💼 **Job Recommendations** | Matched live jobs from Adzuna API + curated seed catalog — sorted by skill overlap with your resume |
| 🔍 **JD Match Analyser** | Paste any job description to get an instant match score, missing keywords, and resume rewrite suggestions |
| 📈 **Skill Development Plan** | Tiered learning plan ("Start Now", "Next", "Optional") with curated resource links based on real job demand |
| ✅ **Resume Quality Checks** | Deterministic ATS-readability checks for headings, measurable outcomes, keyword presence |
| 🛠️ **Resume Builder** | Build a fresh professional resume from guided fields — generates a clean PDF with clickable links |
| 📊 **Downloadable PDF Report** | Full career report with insights, matched jobs, skill plan, and quality checks |
| 👤 **User Authentication** | Register/Login to save your session. Passwords are securely hashed |
| 🔄 **Auto Job Sync** | Job catalog auto-populates from Adzuna on every analysis — no manual setup needed |

---

## 🖥️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit (Python UI framework) |
| **AI Provider** | Google Gemini API (`gemini-3.5-flash`) |
| **Database** | SQLite (job catalog + user accounts) |
| **Job Data** | Adzuna Jobs API + curated seed catalog |
| **PDF Generation** | ReportLab |
| **Resume Parsing** | PyMuPDF (PDF), python-docx (DOCX) |
| **Testing** | pytest — 177 tests, zero API calls |
| **Deployment** | Streamlit Community Cloud (free tier) |

---

## 🚀 How to Run Locally

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

### Step 4 — Set up your environment secrets

```powershell
# Windows
Copy-Item .env.example .env
```

```bash
# macOS / Linux
cp .env.example .env
```

Now open `.env` and fill in your keys:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash

ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
ADZUNA_COUNTRY_CODE=in
```

> 💡 **Get a free Gemini API key** at [aistudio.google.com](https://aistudio.google.com/app/apikey)  
> 💡 **Get free Adzuna credentials** at [developer.adzuna.com](https://developer.adzuna.com/signup)  
> ⚠️ Never commit your `.env` file — it is already in `.gitignore`

### Step 5 — Run the app

```powershell
# Windows
.\.venv\Scripts\streamlit.exe run app\main.py
```

```bash
# macOS / Linux
streamlit run app/main.py
```

The app will open at **[http://localhost:8501](http://localhost:8501)** 🎉

---

## ☁️ Deploying to Streamlit Cloud (Free)

1. Push this repo to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select your repo → Branch: `main` → Main file: `app/main.py`
4. Click **Deploy** — wait ~2 minutes
5. Go to **Settings → Secrets** and paste:

```toml
AI_PROVIDER = "gemini"
GEMINI_API_KEY = "your_actual_key_here"
GEMINI_MODEL = "gemini-3.5-flash"

ADZUNA_APP_ID = "your_app_id"
ADZUNA_APP_KEY = "your_app_key"
ADZUNA_COUNTRY_CODE = "in"
```

6. Click **Save** — app reboots automatically ✅

> **Future updates:** Just `git push origin main` and Streamlit Cloud redeploys automatically!

---

## 🧪 Running Tests

```bash
pytest
```

All 177 tests run with **zero API calls** — they use synthetic data, temporary databases, and mocked AI responses.

```
177 passed in 8.56s
```

---

## 📁 Project Structure

```
Resume_Analyser/
├── app/
│   ├── main.py               # Streamlit entry point
│   ├── config/settings.py    # Env config (reads .env + Streamlit Secrets)
│   ├── components/           # UI components (analysis, jobs, skills, etc.)
│   └── pages/                # Page views (analyze, results, builder, login)
├── services/                 # Business logic (analysis, recommendations, etc.)
├── integrations/             # AI gateways (Gemini, OpenAI) + Adzuna client
├── models/                   # Data models (Job, Resume, Analysis)
├── repositories/             # SQLite repositories
├── reports/                  # PDF report and resume renderers
├── parsers/                  # Resume file parsing (PDF, DOCX, TXT)
├── scripts/                  # Job catalog management scripts
├── data/
│   └── seed_catalog.json     # 20 curated seed job listings (auto-loaded)
├── tests/                    # 177 unit, integration, contract, and UI tests
├── .env.example              # Environment variable template
├── requirements.txt          # Production dependencies
└── README.md
```

---

## 🛡️ Privacy & Security

- ✅ Resume text is sent to Gemini **only after explicit user consent**
- ✅ No resume content is stored in the database — session only
- ✅ Passwords are securely hashed (never stored as plaintext)
- ✅ API keys are read from environment / Streamlit Secrets — never hardcoded
- ✅ All job application URLs validated as real HTTPS links

---

## 📄 License

This project is licensed under the **MIT License** — use it, fork it, build on it.

---

<div align="center">

Built with ❤️ by **Soubhagya Kulkarni**

[![GitHub](https://img.shields.io/badge/GitHub-Soubhagyakulkarni-181717?style=flat-square&logo=github)](https://github.com/Soubhagyakulkarni)

</div>

# 💼 Job Search & Recommendation Application

A complete, production-ready **Job Search & Recommendation** application built using **Python**, **Streamlit**, the **Arbeitnow Public Jobs REST API**, and a persistent **MySQL 8.0** database with **SQLAlchemy** and **PyMySQL**.

The interface faithfully reproduces the modern light dashboard design:
- Pale blue-white background with subtle card borders and shadows.
- Distinct `#6C47FF` purple accents and dark navy headings.
- 3-column desktop layout (Left Navigation/Filters Sidebar, Wide Central Results Feed, Right Insights Column with dynamic charts).
- Responsive mobile/narrow-screen fallback.
- Explainable recommendation ranking: **70% Skill Match + 30% Location Match**.

---

## 📸 Visual Design Highlights

- **Hero Banner:** Lavender-to-light-blue gradient banner featuring a modern desk illustration (laptop, potted plant, coffee mug, and floating skill badges: *AI/ML*, *Data Science*, *Python*).
- **Search Panel:** Inputs for Job Title/Skills, Location, and Work Model, with one-click interactive popular skill chips (`Python`, `Data Analyst`, `Machine Learning`, `AI`, `Cloud`, `SQL`, `Power BI`, `NLP`, `Backend`, `Frontend`).
- **Job Cards:** Company logos/avatars, verified checkmarks, rich metadata rows (location, employment type, salary, relative posted time), pill-shaped skill tags, work model badges (`Remote`, `Hybrid`, `On-site`, `Remote / Hybrid`), save/unsave heart toggles, and "View Details" dialogs.
- **Insights Column:**
  - **Top Recommended Skills:** Horizontal progress bars displaying percentage of active job results mentioning each skill.
  - **Job Type Distribution:** Donut chart showing breakdown across Full-time, Part-time, Contract, and Internship.
  - **Recent Searches:** Real-time log of previous queries with one-click re-run buttons and a "View All" action.
- **Data Integrity & Honesty:** Transparent distinction between Live Arbeitnow listings (predominantly European/Global Remote tech roles) and the curated Benchmark Demo Mode (which matches the visual reference benchmark).

---

## 🏗️ Architecture & Module Organization

```
JobSearch/
├── app.py                      # Main Streamlit application entry point
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── .env                        # Active environment configuration
├── docker-compose.yml          # Optional Docker Compose for local MySQL 8.0
├── README.md                   # Setup guide and documentation
├── .streamlit/
│   └── config.toml             # Streamlit theme & server configuration
├── assets/
│   ├── banner_illustration.svg # Vector SVG desk & skill pills illustration
│   └── reference_screenshot.png# Benchmark reference screenshot
├── sql/
│   └── schema.sql              # MySQL DDL script with all 7 normalized tables
├── database/
│   ├── __init__.py
│   ├── connection.py           # SQLAlchemy engine, connection pooling, init_db
│   ├── models.py               # SQLAlchemy ORM models (Profile, Job, Skill, etc.)
│   └── repository.py           # Bulk upsert, search tracking, saved jobs, analytics
├── services/
│   ├── __init__.py
│   ├── api_client.py           # Arbeitnow API client (retries, timeouts, pagination)
│   ├── normalizer.py           # Token-aware regexes, alias mapping, sanitization
│   ├── ranker.py               # 70/30 explainable ranking engine with tie-breaking
│   └── demo_data.py            # Curated benchmark dataset for Demo Mode
├── ui/
│   ├── __init__.py
│   ├── styles.py               # Custom CSS design system (#6C47FF, cards, badges)
│   ├── components.py           # Job cards, banner, donut charts, progress bars
│   ├── page_search.py          # Search Jobs page
│   ├── page_my_searches.py     # My Searches replay page
│   ├── page_saved_jobs.py      # Saved Jobs bookmark manager
│   ├── page_analytics.py       # Metrics & analytics dashboard
│   ├── page_profile.py         # Candidate profile & search defaults editor
│   └── page_about.py           # Architecture & algorithm documentation
└── tests/
    ├── __init__.py
    ├── test_database.py        # MySQL persistence, duplicate prevention, saved jobs
    ├── test_filtering.py       # Job type, work model, salary filtering tests
    ├── test_normalization.py   # Sanitization, token-awareness (Java vs JS), aliases
    └── test_ranking.py         # 70/30 weighting, normalization, geographic eligibility
```

---

## 🗄️ Normalized MySQL Schema

The application persists all core entities in 7 normalized relational tables:

1. **`profiles`**: Candidate ID, candidate name, preferred skills, preferred location, preferred work model, and timestamps.
2. **`jobs`**: Job ID, provider (`arbeitnow` or `demo`), external unique ID, title, company, location, description, application URL, remote flag, work model, employment type, experience level, salary fields, company logo URL, and timestamps.
   - Enforces `UNIQUE KEY unique_provider_ext (provider, external_id)` to prevent duplicates upon repeated fetches.
3. **`skills`**: Canonical skill names (e.g., `Python`, `Machine Learning`, `PostgreSQL`).
4. **`job_skills`**: Many-to-many junction table between `jobs` and `skills` with foreign keys and cascade deletes.
5. **`searches`**: Search ID, profile ID, query, requested skills, location, JSON filter criteria, result count, and timestamp.
6. **`search_results`**: Junction table recording top ranked job IDs, calculated relevance score, and human-readable match explanation.
7. **`saved_jobs`**: Candidate bookmarks with `UNIQUE KEY unique_profile_job (profile_id, job_id)`.

---

## 🚀 Setup & Installation (Windows PowerShell)

### 1. Prerequisites
- **Python 3.10+** installed and available in PATH.
- **MySQL Server 8.0+** (either local, Docker container, or Cloud MySQL such as Aiven).

### 2. Clone / Open Directory
Open PowerShell in the project directory:
```powershell
cd "c:\Users\SINDHU SURAJ\source\repos\JobSearch"
```

### 3. Create and Activate Virtual Environment
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

*(Note: If PowerShell displays an execution policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

### 4. Install Dependencies
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## ⚙️ Configuration (.env)

Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```

Configure your MySQL connection parameters in `.env`:

### Option A: Local MySQL Server
```ini
DB_HOST=localhost
DB_PORT=3306
DB_NAME=job_search_rec
DB_USER=root
DB_PASSWORD=your_mysql_root_password

ARBEITNOW_API_URL=https://www.arbeitnow.com/api/job-board-api
API_TIMEOUT_SECONDS=10
API_CACHE_TTL_SECONDS=600
DEFAULT_PROFILE_ID=1
```

### Option B: Cloud MySQL (e.g. Aiven Cloud - Pre-configured)
The repository is pre-configured with a working, live cloud MySQL database:
```ini
DB_HOST=mysql-305f07b-sinduvr-3dee.f.aivencloud.com
DB_PORT=13596
DB_NAME=job_search_rec
DB_USER=avnadmin
DB_PASSWORD=your_cloud_mysql_password
```

### Option C: Local Docker MySQL Container
If you prefer running MySQL in Docker:
```powershell
docker-compose up -d
```
This automatically initializes `job_search_rec` with `sql/schema.sql`.

---

## 🗄️ Database Initialization

To manually initialize or verify the schema:
```powershell
python -c "from database.connection import init_db; init_db(); print('Database tables initialized successfully!')"
```

---

## 🏃 Running the Application

Launch Streamlit:
```powershell
python -m streamlit run app.py
```

The application will be accessible at:
👉 **`http://localhost:8501`**

---

## 🧪 Running Automated Tests

Run the complete test suite with verbose output:
```powershell
python -m pytest tests/ -v
```

Expected output:
```
============================= test session starts =============================
tests/test_database.py::test_db_connectivity PASSED                      [  6%]
tests/test_database.py::test_profile_persistence PASSED                  [ 13%]
tests/test_database.py::test_upsert_duplicate_prevention PASSED          [ 20%]
tests/test_database.py::test_saved_job_toggle_persistence PASSED         [ 26%]
tests/test_database.py::test_search_history_persistence PASSED           [ 33%]
tests/test_filtering.py::test_filter_job_types PASSED                    [ 40%]
tests/test_filtering.py::test_filter_work_models PASSED                  [ 46%]
tests/test_filtering.py::test_filter_salary_unknown_handling PASSED      [ 53%]
tests/test_normalization.py::test_sanitize_html_text PASSED              [ 60%]
tests/test_normalization.py::test_token_aware_java_vs_javascript PASSED  [ 66%]
tests/test_normalization.py::test_skill_alias_resolution PASSED          [ 73%]
tests/test_normalization.py::test_determine_work_model_honest_reporting PASSED [ 80%]
tests/test_ranking.py::test_ranking_weights_and_normalization PASSED     [ 86%]
tests/test_ranking.py::test_remote_job_geographic_restriction PASSED     [ 93%]
tests/test_ranking.py::test_stable_tie_breaking PASSED                   [100%]
============================= 15 passed in 3.80s ==============================
```

---

## ⚖️ Recommendation & Ranking Methodology

The matching engine uses an **explainable 70 / 30 formula**:
$$\text{Relevance Score} = (0.70 \times \text{Skill Match}) + (0.30 \times \text{Location Match})$$

### 1. Normalization Across Supplied Criteria
- **Both Skills & Location Provided:** Weighted $70\%$ skills and $30\%$ location.
- **Skills Only Provided:** Score is normalized to $100\%$ of the skill match.
- **Location Only Provided:** Score is normalized to $100\%$ of the location match.
- **Neither Provided:** Ranked strictly by newest timestamp first.

### 2. Token-Aware Skill Extraction & Aliases
- Uses negative lookbehind/lookahead regular expressions (`(?<!\w)...(?!\w)`) to ensure exact token boundaries.
- **False-positive prevention:** `Java` will **never** match `JavaScript`; `C` will **never** match `Cloud` or `CSS`.
- Automatically maps aliases to canonical names:
  - `ML` $\rightarrow$ `Machine Learning`
  - `AI` $\rightarrow$ `AI`
  - `Postgres` $\rightarrow$ `PostgreSQL`
  - `K8s` $\rightarrow$ `Kubernetes`
  - `DL` $\rightarrow$ `Deep Learning`

### 3. Deterministic Location Scoring
- Exact city and country match: **$1.0$ ($100\%$)**
- Sub-part / city match: **$0.9$ ($90\%$)**
- Remote position matching remote applicant: **$0.6$ ($60\%$)**
- Remote position with regional restriction (e.g. *US only*, *Europe only*): **$0.15$ ($15\%$)**
- Non-matching location: **$0.0$ ($0\%$)**

---

## 🌐 Data Coverage & Honest Reporting Policies

1. **Arbeitnow Public API Reality:**
   - Arbeitnow is a free job board primarily covering vacancies in **Germany, Europe, and Global Remote** tech roles.
   - Live searches for Indian locations (e.g., *Bengaluru, India*) will legitimately return 0 results from Arbeitnow.
2. **Curated Demo Mode:**
   - To inspect the benchmark layout with Indian tech firms (*Google, Microsoft, Amazon, Netflix, Flipkart* in Bengaluru) as depicted in the reference screenshot, toggle **Demo Mode** in the sidebar.
   - Demo mode is visibly labeled with a warning banner to guarantee transparent data presentation.
3. **No Invented Fields:**
   - The live API does not provide structured salary ranges or experience levels; these are displayed honestly as `Not provided`.

---

## 🛠️ Troubleshooting

- **MySQL Connection Denied (Error 1045 / 2003):**
  - Verify that MySQL service is running (`Get-Service MySQL*` in PowerShell).
  - Verify `DB_HOST`, `DB_PORT`, `DB_USER`, and `DB_PASSWORD` in your `.env` file.
  - The default pre-configured cloud Aiven instance connects over SSL on port `13596`.
- **API Request Timeouts:**
  - Increase `API_TIMEOUT_SECONDS` in `.env` if internet connection is latent.
  - The API client includes automatic bounded retries with exponential backoff.

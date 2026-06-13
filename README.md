# Debatetrix AI

Debatetrix AI is a Streamlit website for debate intelligence, fact verification, rivalry analysis, and controversy research.

Tagline: **Debates End. Facts Begin.**

## Features

- Gen Z-styled Streamlit interface
- Fact claim breakdown and transparent verification status
- Debate/rivalry brief generator
- India and global fact-check source library
- Public RSS/feed ingestion for supported fact-check websites
- MySQL storage for fetched fact-check items
- Multilingual UI foundation
- Local-first inference status
- Optional BYOK environment hooks for OpenAI and Google Fact Check API

## Run in VS Code

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Or double-click `start_app.bat` on Windows after installing Python.

## Optional API keys

Create a `.env` file or set environment variables:

```text
OPENAI_API_KEY=your_key_here
GOOGLE_FACT_CHECK_API_KEY=your_key_here
LOCAL_MODEL_ENDPOINT=http://localhost:11434
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=debatetrix
```

The default app does not fabricate citations. Without live API integration it performs local risk analysis and routes users to trusted verification sources.

## MySQL setup

Start MySQL, create a user if needed, then open the app and use **Intel Feed -> Setup MySQL**.

You can also run the schema manually:

```powershell
mysql -u root -p < schema.sql
```

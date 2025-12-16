# WisdomTree Daily Summary Bot

This project is a Python-based automation tool designed to fetch, analyze, and summarize the WisdomTree Daily Dashboard. It runs daily via GitHub Actions to create a concise markdown summary of financial data.

## Project Overview

*   **Goal:** Automate the consumption of financial insights from WisdomTree's daily PDF report.
*   **Mechanism:**
    1.  Downloads the specific "Daily Dashboard" PDF from WisdomTree's website.
    2.  Extracts raw text using `PyMuPDF`.
    3.  Estimates processing costs to prevent overruns.
    4.  Sends the text to an LLM via OpenRouter for summarization.
    5.  Archives the summary and logs token usage.
*   **Stack:** Python 3.11, Requests, PyMuPDF, OpenRouter API, GitHub Actions.

## Directory Structure

*   `scripts/`: Contains the core logic (`fetch_and_summarize.py`).
*   `summaries/`: Destination folder for generated Markdown reports (`YYYY-MM-DD.md`) and usage logs (`tokens.log`).
*   `.github/workflows/`: CI/CD configuration for daily scheduling.

## Setup & Usage

### Prerequisites

*   Python 3.11+
*   An OpenRouter API Key

### Installation

```bash
pip install -r requirements.txt
```

### Running Locally

1.  Set the environment variable:
    ```bash
    # Linux/Mac
    export OPENROUTER_API_KEY="your_key_here"

    # Windows (PowerShell)
    $env:OPENROUTER_API_KEY="your_key_here"
    ```
2.  Run the script:
    ```bash
    python scripts/fetch_and_summarize.py
    ```
3.  Output will be generated in the `summaries/` directory.

### Configuration

The script `scripts/fetch_and_summarize.py` contains configurable constants at the top:
*   `MODEL`: The LLM model string (default: "openai/gpt-5.2").
*   `MAX_COST_DOLLARS`: Safety limit for API costs per run.
*   `SUMMARIZE_PROVIDER`: Controls which LLM provider(s) to use for summarization.
    *   `ALL` (default): Runs both OpenRouter and Gemini.
    *   `OPENROUTER`: Runs only OpenRouter.
    *   `GEMINI`: Runs only Gemini.
    *   `NONE`: Skips all LLM summarization.

## Automation

The project is configured to run automatically via GitHub Actions:
*   **Schedule:** Daily at 15:00 UTC (8:00 AM MST).
*   **Workflow:** `.github/workflows/summary.yml`
*   **Secrets:** Requires `OPENROUTER_API_KEY` to be set in the repository secrets.

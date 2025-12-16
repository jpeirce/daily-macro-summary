# Daily Macro Summary Bot

An automated financial intelligence agent that monitors, extracts, scores, and summarizes the [WisdomTree Daily Dashboard](https://www.wisdomtree.com/investments/-/media/us-media-files/documents/resource-library/daily-dashboard.pdf).

This system uses a **Two-Pass Architecture** to ensure accuracy:
1.  **Extraction (Pass 1):** Uses **Gemini 1.5 Pro Vision** to extract raw data (High Yield Spreads, P/E Ratios, Yields) from the PDF charts.
2.  **Deterministic Scoring:** A Python engine calculates "Ground Truth" scores (0-10) for Liquidity, Valuation, Inflation, etc., using rigorous financial formulas (Logarithmic scaling, Historical centering).
3.  **Summarization (Pass 2):** Feeds the PDF and the *Calculated Scores* to two LLMs (**Gemini 3 Pro** and **Grok 4.1 Fast**) to generate a strategic market outlook.

## 🚀 Features

*   **Dual-Model Analysis:** Compares insights from Google (Gemini) and xAI (Grok) side-by-side.
*   **Vision-Native:** Uses Multimodal LLMs to "read" the charts, not just text.
*   **Math-Backed Scoring:** Scores are calculated deterministically to prevent LLM hallucination.
    *   *Liquidity:* Log-scaled High Yield Spread vs. Median.
    *   *Valuation:* S&P 500 P/E centered at 18x.
    *   *Inflation:* 5y5y Breakevens centered at 2.25%.
*   **Live Data Fallback:** Fetches live VIX from Yahoo Finance if missing from the PDF.
*   **HTML Dashboard:** Generates a clean, color-coded HTML report deployed to GitHub Pages.
*   **Daily Email:** Delivers the briefing to your inbox every morning (10:00 AM MST).

## 📊 Benchmark Arena

This repository maintains a separate `benchmark` branch for testing model performance.

*   **Branch:** `benchmark`
*   **Purpose:** Runs **8 different Vision Models** (Claude 3.5/4.5, GPT-4o, Llama 4, Qwen, Nemotron, etc.) against the same PDF.
*   **Difference:** The Benchmark branch *removes* the Ground Truth constraint, allowing models to calculate scores themselves to test their reasoning capabilities.
*   **UI:** Generates an interactive Dropdown/Tabbed HTML report to switch between model outputs.

**To Run the Benchmark:**
```bash
gh workflow run summary.yml --ref benchmark
```

## 🛠️ Setup

### GitHub Secrets
Required secrets for the Action to run:
*   `OPENROUTER_API_KEY`: For Grok/Claude/GPT models.
*   `AI_STUDIO_API_KEY`: For Gemini extraction and summarization.
*   `SMTP_EMAIL`: Sender Gmail address.
*   `SMTP_PASSWORD`: Gmail App Password.
*   `RECIPIENT_EMAIL`: Where to send the report.

### Configuration
The script is controlled via environment variables in `.github/workflows/summary.yml`:
*   `SUMMARIZE_PROVIDER`: `ALL` (runs both), `GEMINI`, or `OPENROUTER`.
*   `OPENROUTER_MODEL`: Model ID (e.g., `x-ai/grok-4.1-fast`).
*   `GEMINI_MODEL`: Model ID (e.g., `gemini-3-pro-preview`).

## 📈 Live Dashboard
View the latest report: **[Daily Macro Summary](https://jpeirce.github.io/daily-macro-summary/)**

## Running Locally
1.  Clone: `git clone https://github.com/jpeirce/daily-macro-summary.git`
2.  Install: `pip install -r requirements.txt`
3.  Set Secrets (in `.env` or shell).
4.  Run: `python scripts/fetch_and_summarize.py`

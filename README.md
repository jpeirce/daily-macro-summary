# Daily Macro Summary Bot

An automated macro strategist that extracts, scores, and summarizes financial data from multiple high-signal sources to produce a strategic market outlook.

The system uses a **Three-Pass Intelligence Architecture** to ensure accuracy and objectivity:

1.  **Extraction (Pass 1 - Vision):** Uses **Gemini 3 Pro Preview** to extract raw numerical data (Spreads, P/E Ratios, Yields, CME Volume/OI) from visual charts and dense tables.
2.  **Ground Truth Engine (Python):**
    *   **Deterministic Scoring:** Calculates scores (0-10) for Liquidity, Valuation, etc., using fixed financial formulas.
    *   **Signal Logic:** Standardizes positioning signals (Directional, Hedging-Vol, Noise) by analyzing the dominance ratio between Futures and Options OI changes.
    *   **Live Analysis:** Fetches real-time S&P 500 trend and 10-Year Treasury Yield (`^TNX`) basis point changes to ensure narrative precision.
    *   **Event Calendar:** Detects Monthly OPEX, Triple Witching, and Month-End rebalancing via a deterministic rules engine.
3.  **Summarization (Pass 3 - Logic Gates):** Feeds extracted data, Ground Truth scores, and the Event Context to an LLM. Strict **Invariant Gates** mandate specific phrasing, while a post-processing **Redaction Scrubber** ensures no directional leakage occurs in sections where the signal is mathematically weak.
4.  **Verification & Validation (Pass 4 - Audit):** A final validator scans the generated narrative to ensure each score's justification stays within its "Metric Whitelist" (e.g., Growth cannot cite Credit spreads) and that no euphemistic directional "leakage" bypassed Pass 3.

## 🚀 Features

*   **Multi-Source Synthesis:** Combines the WisdomTree Daily Dashboard, CME Daily Bulletin (Section 01 & 09), and Yahoo Finance live data.
*   **Rates Curve Intelligence:** Automatically identifies the "Active Tenor" and dominant activity cluster (Short End, Belly, Tens, Long End) across the Treasury futures curve.
*   **Deterministic Signal Gates:** Python-based logic enforces signal labels (Directional, Hedging-Vol, Noise) based on mathematical thresholds (`max(abs(futures), abs(options))`), preventing LLM hallucinations.
*   **Metric Integrity (Whitelist):** Enforces strict "Metric Boundaries"—the LLM is prohibited from misassigning drivers (e.g., citing HY Spreads to justify Growth scores). Post-processing replaces out-of-scope justifications with a revision notice.
*   **Event-Aware Intelligence:** Automatically detects expiry cycles (OPEX/Witching) and downgrades directional conviction when volume/OI signals may be distorted.
*   **Guaranteed Narrative Safety:** 
    *   **Global Constraints:** Explicitly bans "Actor Attribution" (Smart Money, Whales, Institutions, Allocators).
    *   **Euphemism Scrubber:** Surgical regex scrubber redacts both direct directional terms and subtle "leakage" (upside bias, risk-on skew, tilted bullish) from non-directional sections.
*   **Interactive HTML Dashboard:**
    *   **Sticky Status Bar:** Real-time chips for Signal, Direction, Trend, and Participation pinned to the top of the viewport.
    *   **Rates Curve Visual:** Heatmapped table and grid showing OI changes across the front, belly, and long end of the curve.
    *   **Audit Trail:** Collapsible "Data Verification" block with CME row anchors, raw signed deltas, and gate logic tooltips.
    *   **Navigation:** Left-side mini Table of Contents for quick section jumping.
*   **Daily Email:** Delivers the briefing to your inbox every morning.

## 🛠️ Setup

### GitHub Secrets
Required for the GitHub Actions pipeline:
*   `AI_STUDIO_API_KEY`: For Gemini extraction and summarization.
*   `OPENROUTER_API_KEY`: (Optional) Required if using `OPENROUTER` or `ALL` summarization providers.
*   `SMTP_EMAIL`: Sender Gmail address.
*   `SMTP_PASSWORD`: Gmail App Password.
*   `RECIPIENT_EMAIL`: Target email address.

### Configuration
Controlled via environment variables or workflow files:
*   `RUN_MODE`: Set to `PRODUCTION` (Strict Gates), `BENCHMARK` (Visual Reasoning), or `BENCHMARK_JSON` (Pure Data Reasoning).
*   `SUMMARIZE_PROVIDER`: Set to `GEMINI` (default), `OPENROUTER`, or `ALL` (enables side-by-side comparison in the HTML report).
*   `GEMINI_MODEL`: Set to `gemini-3-pro-preview`.

## 🤖 GitHub Actions

The system is automated via GitHub Actions workflows:

### 1. Daily Macro Summary (`daily_macro.yml`)
*   **Schedule:** Runs automatically at **17:00 UTC (10:00 AM MST)** on market days (Mon-Fri).
*   **Manual Trigger:** Go to **Actions** -> **Daily Macro Summary** -> **Run workflow**.
*   **Output:** Updates the `index.html` report on GitHub Pages.

### 2. Benchmark Arena (`benchmark.yml`)
*   **Trigger:** Manual only. Go to **Actions** -> **Benchmark Arena** -> **Run workflow**.
*   **Purpose:** Runs the "Score Yourself" logic against a roster of 7+ top-tier models (Claude 4.5, GPT-5.2, Grok, etc.) using all available PDF inputs.
*   **Output:** Updates the `benchmark.html` report on GitHub Pages.

### 3. Benchmark Arena (Data Only) (`benchmark_data.yml`)
*   **Trigger:** Manual only. Go to **Actions** -> **Benchmark Arena (Data Only)** -> **Run workflow**.
*   **Purpose:** Runs the same "Score Yourself" logic but feeds the models **extracted JSON data** instead of raw PDFs. This isolates reasoning ability from vision/OCR capabilities.
*   **Output:** Updates the `benchmark_data.html` report on GitHub Pages.

## 📈 Live Dashboards
*   **[Daily Macro Summary](https://jpeirce.github.io/daily-macro-summary/)**
*   **[Benchmark Arena (Visual)](https://jpeirce.github.io/daily-macro-summary/benchmark.html)** (Unconstrained Model Testing)
*   **[Benchmark Arena (Data)](https://jpeirce.github.io/daily-macro-summary/benchmark_data.html)** (Pure Reasoning Test)

## Running Locally
1.  **Clone:** `git clone https://github.com/jpeirce/daily-macro-summary.git`
2.  **Install:** `pip install -r requirements.txt`
3.  **Set Env:** Provide API keys in your environment.
4.  **Run:** `python scripts/fetch_and_summarize.py`
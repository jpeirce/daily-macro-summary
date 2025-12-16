# WisdomTree Daily Summary Bot

This GitHub Action runs daily at 8AM Mountain Time to:
- Download the WisdomTree Daily Dashboard PDF
- Extract and summarize its contents via OpenRouter (GPT-5.2 or other)
- Save the result as a markdown file in `summaries/YYYY-MM-DD.md`
- Track token usage to avoid surprise costs

## Setup

1. Add your OpenRouter API key as a GitHub secret named `OPENROUTER_API_KEY`
2. Customize cost limits or models in `scripts/fetch_and_summarize.py`
3. Push to GitHub and you're good to go!

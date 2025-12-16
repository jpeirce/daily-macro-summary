import os
import requests
import fitz  # PyMuPDF
from datetime import datetime

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "openai/gpt-5.2"
PDF_URL = "https://www.wisdomtree.com/investments/-/media/us-media-files/documents/resource-library/daily-dashboard.pdf"

MAX_COST_DOLLARS = 0.10
COST_PER_K_INPUT = 0.00175
COST_PER_K_OUTPUT = 0.014
EST_OUTPUT_TOKENS = 1330

def download_pdf(url, filename):
    response = requests.get(url)
    with open(filename, "wb") as f:
        f.write(response.content)

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join([page.get_text() for page in doc])

def count_tokens(text):
    word_count = len(text.split())
    return int(word_count * 1.33)

def estimate_cost(input_tokens):
    return (input_tokens / 1000) * COST_PER_K_INPUT + (EST_OUTPUT_TOKENS / 1000) * COST_PER_K_OUTPUT

def log_token_usage(date, input_tokens, estimated_cost):
    with open("summaries/tokens.log", "a") as log:
        log.write(f"{date}, input: {input_tokens}, est. cost: ${estimated_cost:.4f}\n")

def summarize(text):
    prompt = (
        "You are a financial analyst AI. Summarize the key data and market signals from the following "
        "Daily Dashboard. The summary should be ~1000 words, include markdown formatting, and highlight "
        "macro trends, valuation signals, sentiment shifts, and market breadth.\n\n" + text
    )
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://chat.openai.com",
        "X-Title": "WisdomTree Daily Summary",
        "Content-Type": "application/json"
    }
    body = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
    return response.json()["choices"][0]["message"]["content"]

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    pdf_path = "daily-dashboard.pdf"
    download_pdf(PDF_URL, pdf_path)
    raw_text = extract_text(pdf_path)
    input_tokens = count_tokens(raw_text)
    cost = estimate_cost(input_tokens)

    if cost > MAX_COST_DOLLARS:
        print(f"⚠️ Estimated cost ${cost:.4f} exceeds limit of ${MAX_COST_DOLLARS:.2f}. Aborting.")
        return

    summary = summarize(raw_text)
    with open(f"summaries/{today}.md", "w", encoding="utf-8") as f:
        f.write(summary)
    log_token_usage(today, input_tokens, cost)

if __name__ == "__main__":
    main()

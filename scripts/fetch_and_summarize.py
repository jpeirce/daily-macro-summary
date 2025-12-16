import os
import requests
import fitz  # PyMuPDF
import smtplib
import google.generativeai as genai
import markdown
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import time # For retry mechanism

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
AI_STUDIO_API_KEY = os.getenv("AI_STUDIO_API_KEY")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
SUMMARIZE_PROVIDER = os.getenv("SUMMARIZE_PROVIDER", "ALL").upper() # ALL, OPENROUTER, GEMINI, NONE
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY", "jpeirce/daily-wisdomtree") # Defaults if not running in Actions

PDF_URL = "https://www.wisdomtree.com/investments/-/media/us-media-files/documents/resource-library/daily-dashboard.pdf"
OPENROUTER_MODEL = "openai/gpt-5.2" # or gpt-4o, etc.
GEMINI_MODEL = "gemini-3-pro-preview" 

def download_pdf(url, filename):
    print(f"Downloading PDF from {url}...")
    response = requests.get(url)
    response.raise_for_status()
    with open(filename, "wb") as f:
        f.write(response.content)
    print("Download complete.")

def extract_text(pdf_path):
    print(f"Extracting text from {pdf_path}...")
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text() for page in doc])
    print(f"Extracted {len(text)} characters.")
    return text

def summarize_openrouter(text):
    print(f"Summarizing with OpenRouter ({OPENROUTER_MODEL})...")
    if not OPENROUTER_API_KEY:
        return "Error: OPENROUTER_API_KEY not set."
        
    prompt = (
        "You are a financial analyst AI. Summarize the key data and market signals from the following "
        "Daily Dashboard. The summary should be ~800 words, include markdown formatting, and highlight "
        "macro trends, valuation signals, sentiment shifts, and market breadth.\n\n" + text
    )
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/jpeirce/daily-wisdomtree",
        "X-Title": "WisdomTree Daily Summary",
        "Content-Type": "application/json"
    }
    body = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        print(f"OpenRouter HTTP Error: {e.response.status_code} - {e.response.text}")
        return f"OpenRouter HTTP Error ({e.response.status_code}): {e.response.text}"
    except Exception as e:
        return f"OpenRouter Error: {e}"

def summarize_gemini(text):
    print(f"Summarizing with Gemini ({GEMINI_MODEL})...")
    if not AI_STUDIO_API_KEY:
        return "Error: AI_STUDIO_API_KEY not set."

    genai.configure(api_key=AI_STUDIO_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    
    prompt = (
        "You are a financial analyst AI. Summarize the key data and market signals from the following "
        "Daily Dashboard text. The summary should be ~800 words, include markdown formatting, and highlight "
        "macro trends, valuation signals, sentiment shifts, and market breadth. "
        "Structure it clearly with headers.\n\n" + text
    )
    
    retries = 3
    for i in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except genai.types.BlockedPromptException as e:
            print(f"Gemini Blocked Prompt Error: {e}")
            return f"Gemini Blocked Prompt Error: {e}"
        except Exception as e:
            if "429" in str(e): # Specific check for rate limit errors in the exception string
                print(f"Gemini Rate Limit Error (429): {e}")
                if i < retries - 1:
                    wait_time = (2 ** i) * 5 # Exponential backoff: 5, 10, 20 seconds
                    print(f"Retrying Gemini in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return "Gemini Error: Rate limit exceeded (429) after multiple retries. Please check your quota."
            else:
                print(f"Gemini Error: {e}")
                return f"Gemini Error: {e}"
    return "Gemini Error: Unknown error after retries." # Should not be reached

def generate_html(today, summary_or, summary_gemini):
    print("Generating HTML report...")
    
    html_or = markdown.markdown(summary_or)
    html_gemini = markdown.markdown(summary_gemini)
    
    css = """
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f4f6f8; }
    h1 { text-align: center; color: #2c3e50; margin-bottom: 30px; }
    .container { display: flex; gap: 20px; flex-wrap: wrap; }
    .column { flex: 1; min-width: 300px; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .column h2 { border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 0; color: #34495e; }
    .footer { text-align: center; margin-top: 40px; font-size: 0.9em; color: #666; }
    @media (max-width: 768px) { .container { flex-direction: column; } }
    """
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WisdomTree Daily Summary - {today}</title>
        <style>{css}</style>
    </head>
    <body>
        <h1>WisdomTree Daily Summary ({today})</h1>
        <div class="container">
            <div class="column">
                <h2>🤖 Gemini ({GEMINI_MODEL})</h2>
                {html_gemini}
            </div>
            <div class="column">
                <h2>🧠 OpenRouter ({OPENROUTER_MODEL})</h2>
                {html_or}
            </div>
        </div>
        <div class="footer">
            Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </body>
    </html>
    """
    
    with open("summaries/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("HTML report generated: summaries/index.html")

def send_email(subject, body_markdown, pages_url):
    print("Sending email...")
    if not (SMTP_EMAIL and SMTP_PASSWORD and RECIPIENT_EMAIL):
        print("Skipping email: Credentials not set.")
        return

    msg = MIMEMultipart()
    msg['From'] = SMTP_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject

    # Add link to web view
    full_body = body_markdown
    if pages_url:
        full_body = f"🌐 **View as Webpage:** {pages_url}\n\n" + full_body

    msg.attach(MIMEText(full_body, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    pdf_path = "daily-dashboard.pdf"
    
    try:
        download_pdf(PDF_URL, pdf_path)
        raw_text = extract_text(pdf_path)
    except Exception as e:
        print(f"Error fetching/reading PDF: {e}")
        return

    summary_or = "OpenRouter summary skipped."
    summary_gemini = "Gemini summary skipped."

    if SUMMARIZE_PROVIDER in ["ALL", "OPENROUTER"]:
        summary_or = summarize_openrouter(raw_text)
    if SUMMARIZE_PROVIDER in ["ALL", "GEMINI"]:
        summary_gemini = summarize_gemini(raw_text)
    
    # Save locally
    os.makedirs("summaries", exist_ok=True)
    with open(f"summaries/{today}_openrouter.md", "w", encoding="utf-8") as f:
        f.write(summary_or)
    with open(f"summaries/{today}_gemini.md", "w", encoding="utf-8") as f:
        f.write(summary_gemini)

    # Generate HTML Report
    generate_html(today, summary_or, summary_gemini)

    # Prepare Email
    email_subject = f"WisdomTree Daily Summary - {today}"
    if SUMMARIZE_PROVIDER == "ALL":
        email_subject += " (A/B Test)"
    else:
        email_subject += f" ({SUMMARIZE_PROVIDER} Only)"

    email_body = (
        f"# Daily WisdomTree Summary ({today})\n\n"
        f"Generated with provider: {SUMMARIZE_PROVIDER}\n\n"
        f"---\n\n"
    )
    if SUMMARIZE_PROVIDER in ["ALL", "GEMINI"]:
        email_body += f"## 🤖 Gemini Summary\n\n{summary_gemini}\n\n---\n\n"
    if SUMMARIZE_PROVIDER in ["ALL", "OPENROUTER"]:
        email_body += f"## 🧠 OpenRouter Summary\n\n{summary_or}\n"
    
    # Determine Pages URL (Best Guess)
    repo_name = GITHUB_REPOSITORY.split("/")[-1] # e.g., daily-wisdomtree
    owner_name = GITHUB_REPOSITORY.split("/")[0] # e.g., jpeirce
    pages_url = f"https://{owner_name}.github.io/{repo_name}/"
    
    send_email(email_subject, email_body, pages_url)

if __name__ == "__main__":
    main()

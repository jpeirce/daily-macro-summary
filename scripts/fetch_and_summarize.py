import os
import requests
import fitz  # PyMuPDF
import smtplib
import google.generativeai as genai
import markdown
import base64
import io
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
OPENROUTER_MODEL = "anthropic/claude-3.5-sonnet" 
GEMINI_MODEL = "gemini-3-pro-preview" 

# ... [SYSTEM_PROMPT remains unchanged] ...

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

def pdf_to_images(pdf_path):
    print(f"Converting PDF to images for Vision...")
    doc = fitz.open(pdf_path)
    images = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom for better resolution
        img_data = pix.tobytes("jpeg")
        base64_img = base64.b64encode(img_data).decode('utf-8')
        images.append(base64_img)
    print(f"Converted {len(images)} pages to images.")
    return images

def summarize_openrouter(pdf_path):
    print(f"Summarizing with OpenRouter ({OPENROUTER_MODEL}) - Using Vision...")
    if not OPENROUTER_API_KEY:
        return "Error: OPENROUTER_API_KEY not set."
        
    # Convert PDF to images
    try:
        images = pdf_to_images(pdf_path)
    except Exception as e:
        return f"OpenRouter Error: PDF to Image conversion failed - {e}"

    # Construct Payload with Images
    content_list = [{"type": "text", "text": SYSTEM_PROMPT}]
    
    for img_b64 in images:
        content_list.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{img_b64}"
            }
        })

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/jpeirce/daily-wisdomtree",
        "X-Title": "WisdomTree Daily Summary",
        "Content-Type": "application/json"
    }
    body = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": content_list}]
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

# ... [summarize_gemini remains unchanged] ...

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    pdf_path = "daily-dashboard.pdf"
    
    try:
        download_pdf(PDF_URL, pdf_path)
        # raw_text extraction is no longer needed for summarization, but keeping extraction fn if needed later
    except Exception as e:
        print(f"Error fetching/reading PDF: {e}")
        return

    summary_or = "OpenRouter summary skipped."
    summary_gemini = "Gemini summary skipped."

    if SUMMARIZE_PROVIDER in ["ALL", "OPENROUTER"]:
        summary_or = summarize_openrouter(pdf_path) # Pass PDF path for Vision
    if SUMMARIZE_PROVIDER in ["ALL", "GEMINI"]:
        summary_gemini = summarize_gemini(pdf_path) # Pass PDF path for Vision
    
    # ... [rest of main remains unchanged] ...
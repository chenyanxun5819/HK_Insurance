import pdfplumber
import sqlite3
import os
import magic  # pip install python-magic
from datetime import datetime

DB_FILE = "aml_profiles.db"
LOG_FILE = "skipped_files.log"

def log_skip(file_path, reason):
    """記錄跳過的檔案與原因"""
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"{datetime.now()} | {file_path} | {reason}\n")

def extract_fields(text):
    """從 PDF 文字中擷取 Name / Nationality / Passport"""
    lines = text.splitlines()
    name = nationality = passport = None
    for line in lines:
        if "Name:" in line:
            name = line.split("Name:")[1].strip()
        elif "Nationality:" in line:
            nationality = line.split("Nationality:")[1].strip()
        elif "Passport no.:" in line or "Passport No:" in line:
            passport = line.split(":")[-1].strip()
    return name, nationality, passport

def process_pdf(pdf_path):
    """檢查檔案是否為有效 PDF 並擷取資料"""
    try:
        mime = magic.from_file(pdf_path, mime=True)
        if mime != "application/pdf":
            log_skip(pdf_path, f"Not a PDF (MIME: {mime})")
            return None

        with pdfplumber.open(pdf_path) as pdf:
            full_text = "\n".join(
                page.extract_text() for page in pdf.pages if page.extract_text()
            )
            if not full_text.strip():
                log_skip(pdf_path, "No text extracted")
                return None
            return extract_fields(full_text)

    except Exception as e:
        log_skip(pdf_path, f"Error: {e}")
        return None

def save_to_db(name, nationality, passport, source_pdf):
    """寫入資料庫，並檢查是否已存在"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 唯一性檢查：避免重複處理同一檔案
    cursor.execute("SELECT 1 FROM profiles WHERE source_pdf = ?", (source_pdf,))
    if cursor.fetchone():
        conn.close()
        return  # 已存在，跳過

    cursor.execute("""
        INSERT INTO profiles (name, nationality, passport_no, source_pdf)
        VALUES (?, ?, ?, ?)
    """, (name, nationality, passport, source_pdf))
    conn.commit()
    conn.close()

# 主程式：批次處理 PDF
pdf_folder = "downloads"
for root, dirs, files in os.walk(pdf_folder):
    for file in files:
        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(root, file)
            result = process_pdf(pdf_path)
            if result:
                name, nationality, passport = result
                save_to_db(name, nationality, passport, pdf_path)
                print(f"✅ Saved: {file}")
            else:
                print(f"⚠️ Skipped: {file}")

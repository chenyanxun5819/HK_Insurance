from google.cloud import storage
import os, tempfile, sqlite3, requests, pdfplumber, random, string
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

IA_INDEX_URL = "https://www.ia.org.hk/en/legislative_framework/circulars/antimoney_laundering/circulars_on_anti-money_laundering_matters.html"
IA_BASE_URL = "https://www.ia.org.hk/en/legislative_framework/circulars/antimoney_laundering/"

# ---------- DB 基礎 ----------
def _connect(db_path):
    return sqlite3.connect(db_path)

def ensure_db_exists(local_path):
    first_time = not os.path.exists(local_path)
    conn = _connect(local_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            name TEXT,
            nationality TEXT,
            passport_no TEXT,
            source_pdf TEXT,
            source_url TEXT,
            created_at TEXT
        )
    """)
    _ensure_column(conn, "profiles", "nationality", "TEXT")
    _ensure_column(conn, "profiles", "passport_no", "TEXT")
    _ensure_column(conn, "profiles", "source_url", "TEXT")
    _ensure_column(conn, "profiles", "created_at", "TEXT")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS processed_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            source_pdf TEXT,
            source_url TEXT,
            processed_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    if first_time:
        print("✅ 建立新 DB 與表結構完成")

def _ensure_column(conn, table, column, type_sql):
    cur = conn.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cur.fetchall()]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_sql}")

def download_db(bucket_name, db_file):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(db_file)
    local_path = os.path.join(tempfile.gettempdir(), db_file)
    try:
        blob.download_to_filename(local_path)
        print(f"✅ 已下載 DB: {local_path}")
    except Exception as e:
        print(f"⚠️ 下載 DB 失敗（可能不存在）: {e}")
        ensure_db_exists(local_path)
    else:
        ensure_db_exists(local_path)
    return local_path

def upload_db(bucket_name, db_file, local_path):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(db_file)
    blob.upload_from_filename(local_path)
    print(f"✅ 已上傳 DB 到 {bucket_name}/{db_file}")

# ---------- 真實爬蟲 ----------
def fetch_pdfs_for_year(year):
    """從年份導覽頁找到該年度的 PDF 連結"""
    print(f"🔍 抓取 {year} 年 PDF 連結...")
    # 先抓年份導覽頁
    index_resp = requests.get(IA_INDEX_URL, timeout=30)
    index_resp.raise_for_status()
    index_soup = BeautifulSoup(index_resp.text, "html.parser")

    # 找到該年度的子頁面連結
    year_link = None
    for a in index_soup.find_all("a", href=True):
        href = a["href"]
        if f"circulars_on_anti-money_laundering_matters_{year}" in href and href.endswith(".html"):
            year_link = urljoin(IA_BASE_URL, href)
            break

    if not year_link:
        # 備用方案：直接用年份 URL 格式
        year_link = f"{IA_BASE_URL}circulars_on_anti-money_laundering_matters_{year}.html"
        print(f"🔄 主頁面未找到年份連結，使用備用 URL: {year_link}")

    # 進入年度頁面找 PDF
    year_resp = requests.get(year_link, timeout=30)
    year_resp.raise_for_status()
    year_soup = BeautifulSoup(year_resp.text, "html.parser")

    pdf_links = []
    for a in year_soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf"):
            full_pdf_url = urljoin(year_link, href)
            pdf_links.append(full_pdf_url)

    print(f"📄 {year} 年找到 {len(pdf_links)} 個 PDF")
    return pdf_links

def process_pdfs(pdf_urls, db_path, year):
    conn = _connect(db_path)
    processed_count = 0
    
    print(f"📊 開始處理 {len(pdf_urls)} 個 PDF 檔案")
    
    for i, url in enumerate(pdf_urls):
        print(f"� 處理 PDF {i+1}/{len(pdf_urls)}: {os.path.basename(url)}")
        
        # 每個 PDF 單獨處理，立即存入 DB 並釋放記憶體
        if process_single_pdf(url, conn, year):
            processed_count += 1
            # 立即提交到資料庫
            conn.commit()
            print(f"✅ PDF {i+1} 處理完成，已存入 DB")
        else:
            print(f"⏩ PDF {i+1} 跳過或失敗")
        
        # 每 5 個 PDF 後強制垃圾回收
        if (i + 1) % 5 == 0:
            import gc
            gc.collect()
            print(f"🧹 已清理記憶體 (處理了 {i+1} 個 PDF)")
    
    conn.close()
    print(f"🎉 全部完成！共成功處理 {processed_count} 個 PDF")
    return processed_count

def process_single_pdf(url, conn, year):
    """處理單個 PDF 檔案，立即存入 DB 並釋放記憶體"""
    # 檢查是否已處理過 - 兼容舊資料庫結構
    try:
        cur = conn.execute("SELECT 1 FROM processed_files WHERE source_pdf=?", (url,))
    except sqlite3.OperationalError:
        # 如果舊欄位不存在，嘗試新欄位結構
        try:
            cur = conn.execute("SELECT 1 FROM processed_files WHERE source_url=?", (url,))
        except sqlite3.OperationalError:
            # 如果表格不存在，建立新表格
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT,
                    source_pdf TEXT,
                    source_url TEXT,
                    processed_at TEXT
                )
            """)
            conn.commit()
            cur = conn.execute("SELECT 1 FROM processed_files WHERE source_url=?", (url,))
    
    if cur.fetchone():
        print(f"⏩ 已處理過，跳過: {os.path.basename(url)}")
        return False

    pdf_path = None
    try:
        # 使用串流下載，減少記憶體使用
        print(f"⬇️ 下載 PDF: {os.path.basename(url)}")
        r = requests.get(url, timeout=60, stream=True)
        r.raise_for_status()
        
        pdf_path = os.path.join(tempfile.gettempdir(), f"temp_{os.getpid()}_{os.path.basename(url)}")
        
        # 串流寫入檔案
        with open(pdf_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # 立即釋放下載物件
        r.close()
        del r
        
    except Exception as e:
        print(f"❌ 下載失敗 {os.path.basename(url)}: {e}")
        return False

    entries_count = 0
    try:
        print(f"🔍 解析 PDF: {os.path.basename(url)}")
        # 處理 PDF
        with pdfplumber.open(pdf_path) as pdf:
            # 限制處理的頁數，避免記憶體爆炸  
            max_pages = min(30, len(pdf.pages))  # 最多 30 頁
            print(f"📖 PDF 共 {len(pdf.pages)} 頁，處理前 {max_pages} 頁")
            
            for page_num in range(max_pages):
                page = pdf.pages[page_num]
                text = page.extract_text() or ""
                
                # 立即處理當前頁面的條目
                entries = extract_sanction_entries(text)
                for entry in entries:
                    if entry['name'] and entry['name'] != 'Unknown' and len(entry['name']) > 3:
                        try:
                            # 嘗試新資料庫結構
                            conn.execute("""
                                INSERT INTO profiles (year, name, nationality, passport_no, source_pdf, source_url, created_at) 
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (year, entry['name'], entry['nationality'], entry['passport_no'], url, url, _now()))
                        except sqlite3.OperationalError:
                            # 如果失敗，使用舊資料庫結構
                            conn.execute("""
                                INSERT INTO profiles (year, name, nationality, passport_no, source_pdf, created_at) 
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (year, entry['name'], entry['nationality'], entry['passport_no'], url, _now()))
                        entries_count += 1
                
                # 立即釋放當前頁面的記憶體
                del text, entries
                
                # 每 10 頁提交一次，避免資料丟失
                if (page_num + 1) % 10 == 0:
                    conn.commit()
                    import gc
                    gc.collect()
                    print(f"  💾 已處理 {page_num + 1} 頁，提交到 DB")
        
        # 記錄已處理的檔案 - 兼容新舊資料庫結構
        try:
            conn.execute("INSERT INTO processed_files (source_pdf, source_url, processed_at) VALUES (?, ?, ?)", (url, url, _now()))
        except sqlite3.OperationalError:
            # 如果新欄位不存在，使用舊格式
            conn.execute("INSERT INTO processed_files (source_pdf) VALUES (?)", (url,))
        print(f"📝 從 {os.path.basename(url)} 提取了 {entries_count} 個條目")
        return True
        
    except Exception as e:
        print(f"❌ PDF 解析錯誤 {os.path.basename(url)}: {e}")
        return False
    finally:
        # 確保清理臨時檔案
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                print(f"🗑️ 已清理臨時檔案: {os.path.basename(pdf_path)}")
            except:
                pass
        
        # 強制垃圾回收
        import gc
        gc.collect()

# ---------- 更新流程 ----------
def get_existing_years(db_path):
    conn = _connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT year FROM profiles WHERE year IS NOT NULL ORDER BY year")
    years = [row[0] for row in cursor.fetchall()]
    conn.close()
    return years

def run_crawler(bucket_name, db_file):
    start_time = datetime.now()
    
    # 1. 從雲端下載現有的 DB 檔案到本地臨時目錄
    db_path = download_db(bucket_name, db_file)
    
    # 2. 檢查已有的年份資料
    years = get_existing_years(db_path)
    current_year = datetime.now().year
    
    # 簡化邏輯：只處理當前年份（自動適應未來年份）
    # 犯罪名單不溯及過往，過去沒有的年份就永遠沒有
    # 2025年可作為測試年份，之後系統會自動處理2026、2027等
    
    if not years:
        # 空 DB，從2001年開始處理到當前年份
        years_to_fetch = list(range(2001, current_year + 1))
        print(f"📅 首次執行 → 處理所有年份: {len(years_to_fetch)} 年 ({min(years_to_fetch)}-{max(years_to_fetch)})")
    else:
        # 有資料，只檢查當前年份是否有新資料
        if current_year not in years:
            years_to_fetch = [current_year]
            print(f"📅 DB 已有年份: {sorted(years)}")
            print(f"📅 檢查新年份: {current_year}")
        else:
            years_to_fetch = [current_year]  # 即使有資料，也檢查當前年份的新檔案
            print(f"📅 DB 已有年份: {sorted(years)}")
            print(f"📅 檢查當前年份新檔案: {current_year}")

    if not years_to_fetch:
        print("📅 沒有新資料需要處理")
        return

    print(f"🎯 計劃處理 {len(years_to_fetch)} 個年份")
    
    total_files = 0
    for i, y in enumerate(years_to_fetch):
        print(f"🔄 開始處理 {y} 年 ({i+1}/{len(years_to_fetch)})...")
        
        # 3. 抓取該年份的所有 PDF 連結
        pdf_urls = fetch_pdfs_for_year(y)
        if pdf_urls:
            print(f"📄 {y} 年找到 {len(pdf_urls)} 個 PDF 檔案")
            
            # 4. 逐個處理 PDF（自動跳過已處理的）
            processed = process_pdfs(pdf_urls, db_path, y)
            total_files += processed
            print(f"📊 {y} 年處理完成，新增 {processed} 個檔案")
            
            # 每年處理完後上傳一次，避免資料丟失
            upload_db(bucket_name, db_file, db_path)
            print(f"☁️ {y} 年資料已備份到雲端")
        else:
            print(f"⚠️ {y} 年沒有找到 PDF 檔案")
        
        # 檢查執行時間，避免超時
        elapsed = (datetime.now() - start_time).total_seconds()
        if elapsed > 3000:  # 50分鐘後停止，避免Cloud Run超時
            print(f"⏰ 執行時間過長 ({elapsed:.0f}s)，暫停處理。剩餘年份下次執行時繼續。")
            break

    # 5. 最終上傳
    upload_db(bucket_name, db_file, db_path)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"✅ 更新完成！共處理 {total_files} 個新檔案，耗時 {elapsed:.2f} 秒")

# ---------- 查詢 ----------
def query_name(bucket_name, db_file, name):
    db_path = download_db(bucket_name, db_file)
    conn = _connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, nationality, passport_no FROM profiles WHERE name LIKE ? COLLATE NOCASE", (f"%{name}%",))
    rows = cursor.fetchall()
    conn.close()
    formatted = [f"{r[0]} | {r[1]} | {r[2]}" for r in rows]
    return (len(formatted) > 0, formatted)

def get_profiles_paginated(bucket_name, db_file, page=1, per_page=20, nationality=None, search_name=None):
    """分頁獲取制裁名單"""
    db_path = download_db(bucket_name, db_file)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查表名 - 新版本用aml_profiles，舊版本用profiles
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        table_name = 'aml_profiles' if 'aml_profiles' in tables else 'profiles'
        
        # 構建查詢條件
        where_conditions = []
        params = []
        
        if nationality:
            where_conditions.append("nationality = ?")
            params.append(nationality)
            
        if search_name:
            where_conditions.append("name LIKE ?")
            params.append(f"%{search_name}%")
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # 查詢總數
        count_query = f"SELECT COUNT(*) FROM {table_name}{where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # 計算分頁
        total_pages = (total + per_page - 1) // per_page
        offset = (page - 1) * per_page
        
        # 查詢數據 - 先檢查欄位是否存在
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        has_source_fields = 'source_pdf' in columns and 'source_url' in columns
        
        if has_source_fields:
            query = f"""
            SELECT name, nationality, passport_no, year, source_pdf, source_url
            FROM {table_name}{where_clause}
            ORDER BY year DESC, name
            LIMIT ? OFFSET ?
            """
        else:
            query = f"""
            SELECT name, nationality, passport_no, year
            FROM {table_name}{where_clause}
            ORDER BY year DESC, name
            LIMIT ? OFFSET ?
            """
            
        cursor.execute(query, params + [per_page, offset])
        rows = cursor.fetchall()
        
        profiles = []
        for row in rows:
            if has_source_fields:
                name, nationality, passport_no, year, source_pdf, source_url = row
                profiles.append({
                    'name': name,
                    'nationality': nationality,
                    'passport_no': passport_no,
                    'year': year,
                    'source_pdf': source_pdf or '',
                    'source_url': source_url or ''
                })
            else:
                name, nationality, passport_no, year = row
                profiles.append({
                    'name': name,
                    'nationality': nationality,
                    'passport_no': passport_no,
                    'year': year,
                    'source_pdf': '',
                    'source_url': ''
                })
        
        conn.close()
        
        return {
            'profiles': profiles,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages
        }
        
    except Exception as e:
        print(f"分頁查詢錯誤: {e}")
        return {
            'profiles': [],
            'total': 0,
            'page': 1,
            'per_page': per_page,
            'total_pages': 0,
            'has_prev': False,
            'has_next': False
        }

def get_stats(bucket_name, db_file):
    """獲取統計信息"""
    db_path = download_db(bucket_name, db_file)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查表名 - 新版本用aml_profiles，舊版本用profiles
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        table_name = 'aml_profiles' if 'aml_profiles' in tables else 'profiles'
        
        # 總數統計
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_profiles = cursor.fetchone()[0]
        
        # 年份統計
        cursor.execute(f"SELECT year, COUNT(*) as count FROM {table_name} GROUP BY year ORDER BY year DESC")
        year_stats = cursor.fetchall()
        
        # 國籍統計
        cursor.execute(f"SELECT nationality, COUNT(*) as count FROM {table_name} GROUP BY nationality ORDER BY count DESC LIMIT 10")
        nationality_stats = cursor.fetchall()
        
        # 最新數據年份
        cursor.execute(f"SELECT MAX(year) FROM {table_name}")
        latest_year = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_profiles': total_profiles,
            'latest_year': latest_year,
            'year_stats': year_stats,
            'nationality_stats': nationality_stats
        }
        
    except Exception as e:
        print(f"統計查詢錯誤: {e}")
        return {
            'total_profiles': 0,
            'latest_year': None,
            'year_stats': [],
            'nationality_stats': []
        }

# ---------- 工具 ----------
def _rand_passport():
    return "E" + "".join(random.choice(string.digits) for _ in range(8))

def _now():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def extract_sanction_entries(text):
    """從 PDF 文字中提取制裁名單條目"""
    import re
    
    entries = []
    lines = text.split('\n')
    current_entry = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 檢查是否是新條目開始 (QDi.XXX 格式)
        if re.match(r'^QDi\.\d+', line):
            # 保存前一個條目
            if current_entry:
                entries.append(finalize_entry(current_entry))
            
            # 開始新條目
            current_entry = {
                'name': '',
                'nationality': 'Unknown',
                'passport_no': 'na',
                'raw_text': line
            }
            
            # 提取姓名 - 更靈活的模式
            name_patterns = [
                r'Name:\s*1:\s*([A-Z\s]+?)\s*2:\s*([A-Z\s]*?)\s*3:\s*([A-Z\s]*?)\s*4:\s*([A-Z\s]*?)(?:\s*Title:|DOB:|Designation:|$)',
                r'Name:\s*1:\s*(\w+)\s*2:\s*(\w*)\s*3:\s*(\w*)\s*4:\s*(\w*)',
                r'Name:\s*([A-Z][A-Z\s]+?)(?:Title:|DOB:|Designation:|$)'
            ]
            
            for pattern in name_patterns:
                name_match = re.search(pattern, line)
                if name_match:
                    if len(name_match.groups()) > 1:
                        # 多個組的情況
                        name_parts = [part.strip() for part in name_match.groups() if part and part.strip()]
                        current_entry['name'] = ' '.join(name_parts)
                    else:
                        # 單個組的情況
                        current_entry['name'] = name_match.group(1).strip()
                    break
        
        elif current_entry:
            # 繼續處理當前條目的其他資訊
            current_entry['raw_text'] += ' ' + line
            
            # 如果姓名還沒找到，繼續嘗試
            if not current_entry['name']:
                name_patterns = [
                    r'Name:\s*1:\s*([A-Z\s]+?)\s*2:\s*([A-Z\s]*?)\s*3:\s*([A-Z\s]*?)\s*4:\s*([A-Z\s]*?)(?:\s*Title:|DOB:|Designation:|Nationality:|$)',
                    r'Name:\s*([A-Z][A-Z\s]+?)(?:Title:|DOB:|Designation:|Nationality:|$)'
                ]
                for pattern in name_patterns:
                    name_match = re.search(pattern, line)
                    if name_match:
                        if len(name_match.groups()) > 1:
                            name_parts = [part.strip() for part in name_match.groups() if part and part.strip()]
                            current_entry['name'] = ' '.join(name_parts)
                        else:
                            current_entry['name'] = name_match.group(1).strip()
                        break
            
            # 提取國籍
            nationality_match = re.search(r'Nationality:\s*([A-Za-z\s]+?)(?:\s+Passport|\s+National|\s+Address|\s+Listed|$)', line)
            if nationality_match:
                current_entry['nationality'] = nationality_match.group(1).strip()
            
            # 提取護照號碼 (多種格式)
            passport_patterns = [
                r'Passport no:\s*([^\s]+(?:\s+number\s+[^\s]+)?)',
                r'Passport number\s*([^\s]+)',
                r'Passport:\s*([^\s]+)'
            ]
            for pattern in passport_patterns:
                passport_match = re.search(pattern, line, re.IGNORECASE)
                if passport_match:
                    passport_value = passport_match.group(1).strip()
                    if passport_value.lower() not in ['na', 'n/a', '']:
                        current_entry['passport_no'] = passport_value
                    break
    
    # 處理最後一個條目
    if current_entry:
        entries.append(finalize_entry(current_entry))
    
    return entries

def finalize_entry(entry):
    """完成條目處理，清理資料"""
    # 清理國籍
    if entry['nationality'] in ['Unknown', 'na', 'n/a', '']:
        entry['nationality'] = 'Unknown'
    
    # 清理護照號碼
    if entry['passport_no'] in ['na', 'n/a', '']:
        entry['passport_no'] = 'na'
    
    # 確保姓名不為空
    if not entry['name'].strip():
        entry['name'] = 'Unknown'
    
    return entry

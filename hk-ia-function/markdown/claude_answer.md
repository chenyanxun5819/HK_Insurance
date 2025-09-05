現在讓我為你創建一個修復後的登入頁面JavaScript代碼：## 問題診斷與解決方案

從你的問題描述和代碼分析，主要問題可能出現在以下幾個地方：

### 1. **Cookie設置問題**
- 在GCP環境中，HTTPS設置可能導致cookie無法正確保存
- Cookie的`secure`標志設置不當

### 2. **認證檢查循環**
- `checkAuth()`函數可能觸發無限重定向
- 認證狀態檢查時機不當

### 3. **Session驗證邏輯**
- `user_manager.verify_session()`可能返回錯誤結果
- Token編碼/解碼問題

## 具體修復步驟：

### 第1步：替換你的login.html中的JavaScript部分
將原來的`<script>`標簽內容替換為上面提供的修復版本。

### 第2步：修改main.py
主要修改點：
1. 添加詳細的日志記錄
2. 修復cookie設置邏輯
3. 改善認證檢查流程
4. 添加錯誤處理

### 第3步：修改query.html中的JavaScript部分
將前端認證代碼替換為修復版本。

## 調試建議：

1. **開啟調試模式**：
   ```python
   app.run(host="0.0.0.0", port=8080, debug=True)
   ```

2. **檢查瀏覽器控制台**：
   - 按F12查看Network標簽
   - 觀察登入請求和響應
   - 查看Cookie是否正確設置

3. **檢查服務器日志**：
   ```bash
   # 查看GCP日志
   gcloud logging read "resource.type=gae_app" --limit=50
   ```

4. **測試步驟**：
   - 清除瀏覽器Cookie和緩存
   - 嘗試登入
   - 檢查是否能在主頁停留

## 常見原因：

1. **Session Token問題**：Firestore中的session可能過期或無效
2. **HTTPS重定向**：GCP的HTTPS強制可能影響cookie
3. **CORS設置**：跨域請求配置問題
4. **時區問題**：Token過期時間計算錯誤

試試這些修復，如果還有問題，請提供瀏覽器控制台的錯誤信息和服務器日志，我可以進一步協助診斷。


### main.py
```
# main.py - 修復版本
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, make_response
from takepdf import run_crawler, query_name, get_profiles_paginated, get_stats
from user_management_firestore import UserManager
from create_admin import create_admin_if_not_exists
import os
import json
import logging

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# 設置日志以便調試
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Firestore 版本
print("🚀 初始化 Firestore 用戶管理器...")
user_manager = UserManager()

# 確保管理員帳戶存在
create_admin_if_not_exists(user_manager)

def require_auth():
    """檢查用戶認證 - 修復版"""
    # 優先從cookie獲取token
    session_token = request.cookies.get('session_token')
    
    # 備選：從Authorization header獲取
    if not session_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            session_token = auth_header[7:]
    
    logger.info(f"Auth check - Token found: {'Yes' if session_token else 'No'}")
    
    if not session_token:
        return {'valid': False, 'message': '請先登入', 'code': 'NO_TOKEN'}
    
    try:
        auth_result = user_manager.verify_session(session_token)
        logger.info(f"Auth result: {auth_result}")
        return auth_result
    except Exception as e:
        logger.error(f"Auth verification error: {str(e)}")
        return {'valid': False, 'message': f'認證失敗: {str(e)}', 'code': 'AUTH_ERROR'}

def require_admin():
    """檢查管理員權限"""
    auth_result = require_auth()
    
    if not auth_result.get('valid'):
        return auth_result
    
    try:
        user = auth_result.get('user', {})
        user_email = user.get('email', '')
        is_admin = user.get('is_admin', False)
        
        if user_email == 'astcws@hotmail.com' or is_admin:
            return auth_result
        else:
            return {'valid': False, 'message': '需要管理員權限', 'code': 'NOT_ADMIN'}
            
    except Exception as e:
        return {'valid': False, 'message': f'權限檢查失敗: {str(e)}', 'code': 'ADMIN_CHECK_ERROR'}

@app.route("/")
def home():
    auth_result = require_auth()
    logger.info(f"Home page auth check: {auth_result}")
    
    if not auth_result.get('valid', False):
        logger.info("Redirecting to login - auth failed")
        return redirect('/login')
    
    logger.info("Auth successful, showing home page")
    return render_template("query.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """用戶登入 - 修復版"""
    if request.method == "GET":
        return render_template("login.html")
    
    try:
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        logger.info(f"Login attempt for email: {email}")
        
        if not email or not password:
            return jsonify({"success": False, "message": "請填寫完整資訊"}), 400
        
        result = user_manager.login_user(email, password)
        logger.info(f"Login result: {result}")
        
        if result['success']:
            # 創建響應
            response = make_response(jsonify(result))
            
            # 設置cookie - 更嚴格的設置
            session_token = result['session_token']
            
            # 檢查是否為HTTPS
            is_secure = request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https'
            
            response.set_cookie(
                'session_token', 
                session_token,
                max_age=7*24*60*60,  # 7天
                httponly=True,
                secure=is_secure,
                samesite='Lax',
                path='/'
            )
            
            logger.info(f"Cookie set successfully. Secure: {is_secure}")
            return response, 200
        else:
            logger.warning(f"Login failed: {result.get('message')}")
            return jsonify(result), 401
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"success": False, "message": f"登入失敗: {str(e)}"}), 500

@app.route("/profile", methods=["GET"])
def profile():
    """獲取用戶個人資料 - 修復版"""
    auth_result = require_auth()
    logger.info(f"Profile request auth result: {auth_result}")
    
    if not auth_result.get('valid', False):
        return jsonify(auth_result), 401
    
    try:
        user = auth_result.get('user', {})
        
        # 獲取查詢統計
        query_stats = user_manager.check_query_limit(user['id'])
        
        return jsonify({
            "success": True,
            "user": {
                "email": user.get('email', ''),
                "is_admin": user.get('is_admin', False),
                "membership_level": user.get('membership_level', 'basic')
            },
            "query_stats": query_stats
        }), 200
    except Exception as e:
        logger.error(f"Profile error: {str(e)}")
        return jsonify({"success": False, "message": f"獲取用戶資料失敗: {str(e)}"}), 500

@app.route("/logout", methods=["POST"])
def logout():
    """用戶登出"""
    try:
        session_token = request.cookies.get('session_token')
        if session_token:
            user_manager.logout_user(session_token)
        
        response = make_response(jsonify({"success": True, "message": "登出成功"}))
        response.set_cookie('session_token', '', expires=0, path='/')
        return response, 200
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({"success": False, "message": f"登出失敗: {str(e)}"}), 500

@app.route("/query", methods=["GET"])
def query():
    # 檢查用戶認證
    auth_result = require_auth()
    if not auth_result.get('valid', False):
        return jsonify(auth_result), 401
    
    user = auth_result['user']
    
    # 檢查查詢限制
    query_limit_check = user_manager.check_query_limit(user['id'])
    if not query_limit_check['can_query']:
        return jsonify({
            "success": False, 
            "message": f"已達到每日查詢限制 ({query_limit_check['daily_limit']} 次)",
            "query_stats": query_limit_check
        }), 429
    
    name = request.args.get("name")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    if not name:
        return jsonify({"error": "缺少 name 參數"}), 400
    
    try:
        # 記錄查詢
        user_manager.log_query(user['id'], 'name_search', json.dumps({'name': name, 'page': page}))
        
        # AML 查詢邏輯保持不變 (仍使用 SQLite)
        if os.path.exists('aml_profiles.db'):
            import sqlite3
            
            conn = sqlite3.connect('aml_profiles.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in cursor.fetchall()]
            table_name = 'aml_profiles' if 'aml_profiles' in tables else 'profiles'
            
            count_query = f"SELECT COUNT(*) FROM {table_name} WHERE LOWER(name) LIKE LOWER(?)"
            cursor.execute(count_query, [f"%{name}%"])
            total = cursor.fetchone()[0]
            
            if total == 0:
                conn.close()
                return jsonify({"found": False, "matches": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0}), 200
            
            total_pages = (total + per_page - 1) // per_page
            offset = (page - 1) * per_page
            
            data_query = f"SELECT * FROM {table_name} WHERE LOWER(name) LIKE LOWER(?) LIMIT ? OFFSET ?"
            cursor.execute(data_query, [f"%{name}%", per_page, offset])
            records = cursor.fetchall()
            
            column_names = [description[0] for description in cursor.description]
            
            matches = []
            for record in records:
                record_dict = dict(zip(column_names, record))
                matches.append(record_dict)
            
            conn.close()
            
            return jsonify({
                "found": True,
                "matches": matches,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages
            }), 200
        else:
            return jsonify({"error": "資料庫檔案不存在"}), 500
            
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        return jsonify({"error": f"查詢失敗: {str(e)}"}), 500

# 其他路由保持不變...

if __name__ == "__main__":
    print("🎉 Firestore 版本啟動完成!")
    app.run(host="0.0.0.0", port=8080, debug=True)  # 開發時啟用debug
```

# javascript 不完整
```
// 修復後的前端認證代碼
// 全域變數
let currentPage = 1;
let totalPages = 1;
let isLoading = false;
let currentNationality = '';
let currentSearchName = '';
let currentUser = null;
let authCheckInProgress = false;

// 認證相關函數 - 修復版
async function checkAuth() {
    // 防止重複檢查
    if (authCheckInProgress) {
        console.log('Auth check already in progress');
        return false;
    }
    
    authCheckInProgress = true;
    
    try {
        console.log('開始檢查認證狀態...');
        
        const response = await fetch('/profile', {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        console.log('認證響應狀態:', response.status);
        
        if (response.ok) {
            const result = await response.json();
            console.log('認證結果:', result);
            
            if (result.success && result.user) {
                currentUser = result.user;
                updateUserBar(result.user, result.query_stats);
                return true;
            } else {
                console.log('認證失敗: 無效的響應數據');
                return false;
            }
        } else {
            console.log('認證失敗: HTTP', response.status);
            return false;
        }
    } catch (error) {
        console.error('認證檢查異常:', error);
        return false;
    } finally {
        authCheckInProgress = false;
    }
}

function updateUserBar(user, queryStats) {
    const userBar = document.getElementById('userBar');
    const userEmail = document.getElementById('userEmail');
    const queryQuota = document.getElementById('queryQuota');
    const adminBtn = document.getElementById('adminBtn');

    if (!userBar || !userEmail || !queryQuota) {
        console.error('找不到用戶界面元素');
        return;
    }

    userEmail.textContent = user.email;

    if (queryStats) {
        if (queryStats.daily_limit === Infinity || queryStats.daily_limit === -1) {
            queryQuota.textContent = `查詢額度: 無限制`;
        } else {
            queryQuota.textContent = `查詢額度: ${queryStats.remaining}/${queryStats.daily_limit}`;
        }
    } else {
        queryQuota.textContent = '查詢額度: 載入中...';
    }

    // 顯示管理員按鈕（如果用戶是管理員）
    if (adminBtn) {
        if (user.is_admin) {
            adminBtn.style.display = 'block';
        } else {
            adminBtn.style.display = 'none';
        }
    }

    userBar.style.display = 'flex';
    console.log('用戶欄位已更新');
}

async function logout() {
    try {
        console.log('開始登出...');
        const response = await fetch('/logout', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        console.log('登出響應狀態:', response.status);
        
        // 無論響應如何，都清除本地狀態並跳轉
        currentUser = null;
        window.location.href = '/login';
    } catch (error) {
        console.error('登出錯誤:', error);
        // 即使出錯也跳轉到登入頁
        window.location.href = '/login';
    }
}

function updateQueryStats(queryStats) {
    const queryQuota = document.getElementById('queryQuota');
    if (queryStats && queryQuota) {
        if (queryStats.daily_limit === Infinity || queryStats.daily_limit === -1) {
            queryQuota.textContent = `查詢額度: 無限制`;
        } else {
            queryQuota.textContent = `查詢額度: ${queryStats.remaining}/${queryStats.daily_limit}`;
        }
    }
}

// DOM 元素
const nameSearch = document.getElementById('nameSearch');
const nationalityFilter = document.getElementById('nationalityFilter');
const searchBtn = document.getElementById('searchBtn');
const clearBtn = document.getElementById('clearBtn');
const searchResult = document.getElementById('searchResult');
const statsInfo = document.getElementById('statsInfo');
const pageInfo = document.getElementById('pageInfo');
const tableBody = document.getElementById('tableBody');
const pagination = document.getElementById('pagination');

// 初始化 - 修復版
document.addEventListener('DOMContentLoaded', async function () {
    console.log('頁面載入完成，開始初始化...');
    
    // 首先檢查認證
    const isAuthenticated = await checkAuth();
    console.log('認證狀態:', isAuthenticated);
    
    if (!isAuthenticated) {
        console.log('認證失敗，跳轉到登入頁');
        // 添加短暫延遲，避免過快跳轉
        setTimeout(() => {
            window.location.href = '/login';
        }, 100);
        return;
    }

    console.log('認證成功，初始化應用...');

    // 載入初始數據
    try {
        await loadStats();
        await loadProfiles();
    } catch (error) {
        console.error('初始化數據載入失敗:', error);
    }

    // 事件監聽
    if (searchBtn) searchBtn.addEventListener('click', performSearch);
    if (clearBtn) clearBtn.addEventListener('click', clearFilters);

    if (nameSearch) {
        nameSearch.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') performSearch();
        });
    }

    if (nationalityFilter) {
        nationalityFilter.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') performSearch();
        });
    }

    console.log('應用初始化完成');
});

// 載入統計資訊
async function loadStats() {
    try {
        const response = await fetch('/stats', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();

        if (data.error) {
            statsInfo.textContent = '統計資訊載入失敗';
            return;
        }

        const totalText = `總計 ${data.total_profiles.toLocaleString()} 筆制裁資料`;
        const yearText = `涵蓋 ${data.year_stats.length} 個年份 (${data.year_stats[data.year_stats.length - 1]?.year}-${data.year_stats[0]?.year})`;
        statsInfo.textContent = `${totalText} • ${yearText}`;

    } catch (error) {
        console.error('載入統計失敗:', error);
        statsInfo.textContent = '統計資訊載入失敗';
    }
}

// 載入制裁名單
async function loadProfiles(page = 1, nationality = '') {
    if (isLoading) return;

    isLoading = true;
    tableBody.innerHTML = '<tr><td colspan="5" class="loading">正在載入資料...</td></tr>';

    try {
        const params = new URLSearchParams({
            page: page,
            nationality: nationality
        });

        const response = await fetch(`/profiles?${params}`, {
            credentials: 'include'
        });

        if (response.status === 401) {
            console.log('認證過期，跳轉到登入頁');
            window.location.href = '/login';
            return;
        }

        if (response.status === 429) {
            const data = await response.json();
            showTableMessage(data.message || '已達到查詢限制', 'error');
            updateQueryStats(data.query_stats);
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // 更新查詢統計
        if (data.query_stats) {
            updateQueryStats(data.query_stats);
        }

        currentPage = data.page;
        totalPages = data.total_pages;
        currentNationality = nationality;

        renderTable(data.profiles, page);
        renderPagination(data);
        updatePageInfo(data);

        // 確保分頁控制在瀏覽模式下顯示
        pagination.style.display = 'flex';

    } catch (error) {
        console.error('載入資料失敗:', error);
        tableBody.innerHTML = `<tr><td colspan="5" class="error">載入失敗: ${error.message}</td></tr>`;
    } finally {
        isLoading = false;
    }
}

// 渲染表格
function renderTable(profiles, page) {
    if (!profiles || profiles.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 2rem; color: #666;">沒有找到符合條件的資料</td></tr>';
        return;
    }

    const startIndex = (page - 1) * 20;
    tableBody.innerHTML = profiles.map((profile, index) => `
        <tr>
            <td>${startIndex + index + 1}</td>
            <td><strong>${escapeHtml(profile.name || '')}</strong></td>
            <td>${escapeHtml(profile.nationality || '')} ${profile.year ? `<span class="badge">${profile.year}</span>` : ''}</td>
            <td>${escapeHtml(profile.passport_no || '')}</td>
            <td>${profile.year || '-'}</td>
        </tr>
    `).join('');
}

// 渲染分頁
function renderPagination(data) {
    if (!data || data.total_pages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let html = '';

    // 上一頁
    const hasPrev = data.page > 1;
    html += `<button ${!hasPrev ? 'disabled' : ''} onclick="changePage(${data.page - 1})">‹ 上一頁</button>`;

    // 頁碼
    const startPage = Math.max(1, data.page - 2);
    const endPage = Math.min(data.total_pages, data.page + 2);

    if (startPage > 1) {
        html += `<button onclick="changePage(1)">1</button>`;
        if (startPage > 2) html += `<span>...</span>`;
    }

    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="${i === data.page ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
    }

    if (endPage < data.total_pages) {
        if (endPage < data.total_pages - 1) html += `<span>...</span>`;
        html += `<button onclick="changePage(${data.total_pages})">${data.total_pages}</button>`;
    }

    // 下一頁
    const hasNext = data.page < data.total_pages;
    html += `<button ${!hasNext ? 'disabled' : ''} onclick="changePage(${data.page + 1})">下一頁 ›</button>`;

    pagination.innerHTML = html;
}

// 更新頁面資訊
function updatePageInfo(data) {
    if (!data) return;
    
    const start = (data.page - 1) * (data.per_page || 50) + 1;
    const end = Math.min(data.page * (data.per_page || 50), data.total_profiles || 0);
    pageInfo.textContent = `第 ${data.page} 頁，共 ${data.total_pages} 頁 (顯示 ${start}-${end}，共 ${(data.total_profiles || 0).toLocaleString()} 筆)`;
}

// 換頁
function changePage(page) {
    if (page < 1 || page > totalPages || isLoading) return;

    // 如果當前是搜尋模式，使用搜尋分頁
    if (currentSearchName) {
        loadNameSearchResults(currentSearchName, page);
    } else {
        // 瀏覽模式，使用一般分頁
        loadProfiles(page, currentNationality);
    }
}

// HTML 轉義
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 在表格中顯示訊息
function showTableMessage(message, type = 'info') {
    const color = type === 'error' ? '#c53030' : '#666';
    pageInfo.textContent = message;
    tableBody.innerHTML = `
        <tr>
            <td colspan="5" style="text-align: center; padding: 2rem; color: ${color};">
                ${escapeHtml(message)}
            </td>
        </tr>
    `;
    pagination.style.display = 'none';
}

// 執行搜尋
async function performSearch() {
    const name = nameSearch?.value.trim() || '';
    const nationality = nationalityFilter?.value.trim() || '';

    if (searchResult) searchResult.innerHTML = '';

    // 判斷是否有查詢條件
    const hasSearchConditions = name || nationality;

    if (hasSearchConditions) {
        // 查詢模式：顯示查詢結果在表格中
        if (name) {
            // 有姓名查詢時，載入分頁查詢結果
            loadNameSearchResults(name, 1);
        } else if (nationality) {
            // 只有國籍過濾時，載入過濾後的分頁資料
            loadProfiles(1, nationality);
        }
    } else {
        // 瀏覽模式：載入完整資料庫
        currentSearchName = '';
        loadProfiles(1, '');
    }
}

// 載入姓名查詢結果（分頁）
async function loadNameSearchResults(name, page = 1) {
    if (isLoading) return;

    isLoading = true;
    tableBody.innerHTML = '<tr><td colspan="5" class="loading">正在查詢...</td></tr>';

    try {
        const params = new URLSearchParams({
            name: name,
            page: page,
            per_page: 20
        });

        const response = await fetch(`/query?${params}`, {
            credentials: 'include'
        });

        if (response.status === 401) {
            window.location.href = '/login';
            return;
        }

        if (response.status === 429) {
            const data = await response.json();
            showTableMessage(data.message || '已達到查詢限制', 'error');
            updateQueryStats(data.query_stats);
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // 更新查詢統計
        if (data.query_stats) {
            updateQueryStats(data.query_stats);
        }

        if (!data.found || data.total === 0) {
            showTableMessage('沒有找到相符的姓名資料', 'info');
            return;
        }

        // 設置當前查詢狀態
        currentSearchName = name;
        currentPage = data.page;
        totalPages = data.total_pages;
        currentNationality = '';

        // 渲染查詢結果
        renderSearchResultTable(data.matches, page);
        renderSearchPagination(data);
        updateSearchPageInfo(data, name);

        // 確保分頁控制顯示
        pagination.style.display = 'flex';

    } catch (error) {
        showTableMessage(`查詢失敗: ${error.message}`, 'error');
    } finally {
        isLoading = false;
    }
}

// 清除過濾條件
function clearFilters() {
    if (nameSearch) nameSearch.value = '';
    if (nationalityFilter) nationalityFilter.value = '';
    if (searchResult) searchResult.innerHTML = '';
    currentSearchName = '';
    loadProfiles(1, '');
}

// 渲染查詢結果表格
function renderSearchResultTable(profiles, page) {
    if (!profiles || profiles.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 2rem; color: #666;">沒有找到符合條件的資料</td></tr>';
        return;
    }

    const startIndex = (page - 1) * 20;
    tableBody.innerHTML = profiles.map((profile, index) => `
        <tr>
            <td>${startIndex + index + 1}</td>
            <td><strong>${escapeHtml(profile.name || '')}</strong></td>
            <td>${escapeHtml(profile.nationality || '')} ${profile.year ? `<span class="badge">${profile.year}</span>` : ''}</td>
            <td>${escapeHtml(profile.passport_no || '')}</td>
            <td>${profile.year || '-'}</td>
        </tr>
    `).join('');
}

// 渲染查詢結果分頁
function renderSearchPagination(data) {
    if (!data || data.total_pages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let html = '';

    // 上一頁
    const hasPrev = data.page > 1;
    html += `<button ${!hasPrev ? 'disabled' : ''} onclick="changeSearchPage(${data.page - 1})">‹ 上一頁</button>`;

    // 頁碼
    const startPage = Math.max(1, data.page - 2);
    const endPage = Math.min(data.total_pages, data.page + 2);

    if
```

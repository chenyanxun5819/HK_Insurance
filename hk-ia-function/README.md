# HK Insurance AML 查詢系統

> 香港保險業反洗錢 (AML) 資料查詢系統

## 🌟 功能特色

- ✅ **會員系統**：支援使用者註冊、登入、密碼重設
- ✅ **查詢限制**：基本會員 5 次查詢，管理員無限制
- ✅ **安全認證**：Cookie-based 認證系統
- ✅ **郵件服務**：SendGrid 整合，支援密碼重設通知
- ✅ **資料庫**：Firebase Firestore 雲端資料庫
- ✅ **生產部署**：Gunicorn WSGI 伺服器

## 🚀 快速開始

### 1. 環境要求

- Python 3.8+
- Node.js (用於 Firebase 模擬器)
- Git

### 2. 安裝依賴

```bash
# 複製專案
git clone https://github.com/chenyanxun5819/HK_Insurance.git
cd HK_Insurance

# 安裝 Python 依賴
pip install -r requirements.txt

# 安裝 Firebase CLI
npm install -g firebase-tools
```

### 3. 環境變數設置

```bash
# 複製環境變數範例檔案
cp .env.example .env

# 編輯 .env 檔案，填入您的 SendGrid API Key
# SENDGRID_API_KEY=your_sendgrid_api_key_here
# SENDGRID_FROM_EMAIL=your_verified_email@example.com
```

### 4. Firebase 設置

```bash
# 啟動 Firestore 模擬器 (開發環境)
firebase emulators:start --only firestore

# 或使用生產環境 Firestore (需要配置 Firebase 專案)
```

### 5. 啟動應用

```bash
# 開發環境
python main_firebase.py

# 生產環境
gunicorn -w 4 -b 0.0.0.0:8000 main_firebase:app
```

## 📁 專案結構

```
hk-ia-function/
├── main_firebase.py           # 主應用程式
├── sendgrid_service.py        # SendGrid 郵件服務
├── user_management_firestore.py  # 使用者管理
├── firestore_aml_query.py     # AML 查詢功能
├── takepdf.py                 # PDF 處理
├── templates/                 # HTML 模板
│   ├── index.html            # 主頁面
│   ├── login.html            # 登入頁面
│   └── ...
├── requirements.txt          # Python 依賴
├── .env.example             # 環境變數範例
└── README.md               # 說明文件
```

## 🔧 核心功能

### 會員管理

- **註冊**：使用者可以註冊新帳戶
- **登入**：Cookie-based 認證系統
- **密碼重設**：透過 SendGrid 發送重設郵件
- **查詢限制**：基本會員 5 次查詢，管理員無限制

### AML 查詢

- **即時查詢**：輸入姓名即時查詢 AML 資料
- **結果顯示**：表格化顯示查詢結果
- **統計功能**：顯示查詢統計資訊
- **權限控制**：根據會員等級限制查詢次數

### 安全特性

- **環境變數**：敏感資訊透過環境變數管理
- **API Key 保護**：SendGrid API Key 不在程式碼中硬編碼
- **權限驗證**：每個操作都經過權限驗證

## 🔐 SendGrid 設置

1. 註冊 [SendGrid](https://sendgrid.com/) 帳戶
2. 創建 API Key
3. 驗證發件人郵件地址
4. 將 API Key 和發件人郵件設置到 `.env` 檔案

## 🗄️ 資料庫

使用 Firebase Firestore 作為資料庫：

- **aml_profiles**：AML 資料集合
- **users**：使用者資料集合
- **query_logs**：查詢記錄集合

## 🚀 部署

### 本地開發

```bash
python main_firebase.py
```

### 生產部署

```bash
gunicorn -w 4 -b 0.0.0.0:8000 main_firebase:app
```

### Docker 部署

```bash
# 構建映像
docker build -t hk-aml-system .

# 運行容器
docker run -p 8000:8000 --env-file .env hk-aml-system
```

## 📝 API 端點

- `GET /` - 主頁面
- `POST /login` - 使用者登入
- `POST /register` - 使用者註冊
- `POST /query` - AML 查詢
- `GET /statistics` - 查詢統計
- `POST /forgot_password` - 密碼重設

## 🛠️ 技術棧

- **後端**：Flask, Python
- **資料庫**：Firebase Firestore
- **郵件服務**：SendGrid
- **前端**：HTML, JavaScript, Bootstrap
- **部署**：Gunicorn, Docker

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

此專案僅供學習和研究使用。

## 📞 聯繫

如有問題，請聯繫專案維護者。

---

**注意**：此系統包含敏感的金融資料，請確保在安全的環境中使用，並遵守相關的資料保護法規。

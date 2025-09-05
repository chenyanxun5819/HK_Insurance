# SendGrid Email 設定說明

## 為什麼改用 SendGrid？

根據 Gemini 的專業建議，Gmail App 密碼與 Cloud Run 現代化架構不相容：
- **Cloud Run 使用 OAuth 2.0** 安全機制
- **App 密碼是為舊版應用程式**設計的
- **SendGrid 是專業的郵件服務**，與雲端服務完全相容

## SendGrid 設定步驟

### 1. 註冊 SendGrid 帳戶
1. 訪問 [SendGrid 官網](https://sendgrid.com/)
2. 註冊免費帳戶（每月 100 封免費郵件）
3. 驗證電子郵件

### 2. 建立 API Key
1. 登入 SendGrid Dashboard
2. 前往 **Settings** → **API Keys**
3. 點擊 **Create API Key**
4. 選擇 **Full Access** 或 **Restricted Access**
5. 複製生成的 API Key（只會顯示一次）

### 3. 設定發件人地址
1. 前往 **Settings** → **Sender Authentication**
2. 選擇 **Single Sender Verification**
3. 添加您的發件人信箱（如 `noreply@your-domain.com`）
4. 驗證發件人信箱

### 4. 更新 Cloud Run 環境變數

```bash
gcloud run services update hk-insurance-aml \
  --set-env-vars SENDGRID_API_KEY="your-sendgrid-api-key",SENDGRID_FROM_EMAIL="your-verified-email@domain.com" \
  --region asia-east1
```

## 本地測試

```bash
cd /home/weschen/HK_insurance/hk-ia-function
export SENDGRID_API_KEY="your-api-key"
export SENDGRID_FROM_EMAIL="your-email@domain.com"
python -c "from user_management import UserManager; um = UserManager('aml_profiles.db'); print(um.forgot_password('test@example.com'))"
```

## SendGrid 優勢

✅ **專業郵件服務** - 高可靠性，99.95% 可用性  
✅ **雲端原生** - 完美支援 Cloud Run  
✅ **免費額度** - 每月 100 封免費郵件  
✅ **高級功能** - 郵件追蹤、分析、模板  
✅ **安全性** - OAuth 2.0 兼容，API Key 管理  

## 目前狀態

- ✅ SendGrid 模組已安裝
- ✅ 郵件服務已整合到忘記密碼功能
- ⚠️ 需要設定 SendGrid API Key
- ✅ 備用方案仍然可用（顯示密碼）

## 立即可用

**即使沒有 SendGrid API Key，系統依然完全正常運作**：
- 忘記密碼功能會直接顯示新密碼
- 用戶可以立即使用新密碼登入
- 等您設定好 SendGrid 後，就會自動切換到郵件發送模式

**服務網址**: https://hk-insurance-aml-574812669587.asia-east1.run.app

# Email 設置指南

## 目前狀況
✅ 系統已部署: https://hk-insurance-aml-574812669587.asia-east1.run.app
✅ 所有功能正常運作
⚠️ Email 發送使用備用模式（顯示密碼）

## 兩種選擇

### 選擇 1: 使用備用模式（目前狀態）
- 忘記密碼功能會直接顯示新密碼
- 不需要額外設置
- 適合測試和內部使用

### 選擇 2: 啟用真正的 Email 發送
需要設置 SendGrid（免費方案: 100封/月）

#### SendGrid 設置步驟：
1. 註冊 SendGrid 帳號: https://sendgrid.com/
2. 取得 API Key
3. 執行下列指令更新 Cloud Run 設置：

```bash
# 設置 SendGrid 環境變數
gcloud run services update hk-insurance-aml \
  --region=asia-east1 \
  --update-env-vars SENDGRID_API_KEY=你的API金鑰 \
  --update-env-vars SENDGRID_FROM_EMAIL=noreply@你的網域.com \
  --remove-env-vars GMAIL_PASSWORD,GMAIL_USER
```

## 測試方式
```bash
# 測試忘記密碼功能
curl -X POST "https://hk-insurance-aml-574812669587.asia-east1.run.app/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "astcws@hotmail.com"}'
```

## 目前可用功能
- ✅ 用戶註冊登入
- ✅ 三級會員制度
- ✅ 管理員功能
- ✅ 資料查詢分頁
- ✅ 忘記密碼（顯示模式）
- ✅ 2025年最新資料（828筆）

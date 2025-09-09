# SendGrid Email 設置指南

## 步驟 1: 註冊 SendGrid 帳號

1. 前往 [SendGrid 官網](https://sendgrid.com/) 點擊 "Start for Free"
2. 填寫註冊資訊：
   - Email: 您的郵箱
   - Password: 設定密碼
   - Company: HK Insurance AML
   - Website: 可填 https://hk-insurance-aml-574812669587.asia-east1.run.app

3. 驗證 Email 並完成註冊

## 步驟 2: 取得 API Key

1. 登入 SendGrid Dashboard
2. 點擊左側選單 "Settings" → "API Keys"
3. 點擊 "Create API Key"
4. 選擇 "Full Access" 
5. 命名為 "HK-Insurance-AML"
6. 點擊 "Create & View"
7. **重要**: 複製 API Key（只會顯示一次）

## 步驟 3: 驗證發件人身份

1. 在 SendGrid Dashboard 點擊 "Settings" → "Sender Authentication"
2. 點擊 "Single Sender Verification"
3. 點擊 "Create New Sender"
4. 填寫資訊：
   - From Name: HK Insurance AML System
   - From Email: 您的郵箱（或創建專用郵箱）
   - Reply To: 同上
   - Company: HK Insurance
   - Address: 可填寫公司地址
5. 點擊 "Create"
6. 到您的郵箱點擊驗證連結

## 步驟 4: 更新 Cloud Run 環境變數

取得 API Key 後，執行以下指令：

```bash
# 設置 SendGrid 環境變數（請替換 YOUR_API_KEY 和 YOUR_VERIFIED_EMAIL）
gcloud run services update hk-insurance-aml \\
  --region=asia-east1 \\
  --update-env-vars SENDGRID_API_KEY=YOUR_API_KEY \\
  --update-env-vars SENDGRID_FROM_EMAIL=YOUR_VERIFIED_EMAIL \\
  --remove-env-vars GMAIL_PASSWORD,GMAIL_USER

# 等待部署完成
echo "部署完成！現在可以發送郵件了。"
```

## 步驟 5: 測試郵件發送

```bash
# 測試忘記密碼功能
curl -X POST "https://hk-insurance-aml-574812669587.asia-east1.run.app/forgot-password" \\
  -H "Content-Type: application/json" \\
  -d '{"email": "您的測試信箱"}'
```

## SendGrid 免費方案限制

- 每月 100 封郵件
- 每日最多 100 封
- 適合小型應用使用

## 故障排除

如果郵件發送失敗：
1. 檢查 API Key 是否正確
2. 確認發件人信箱已驗證
3. 檢查 SendGrid 帳號狀態
4. 查看 Cloud Run 日誌：`gcloud logs read --service=hk-insurance-aml`

---

**準備好 API Key 和驗證郵箱後，告訴我，我會幫您完成配置！**

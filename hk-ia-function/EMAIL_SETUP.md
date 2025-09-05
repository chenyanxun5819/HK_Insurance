# Email 設定說明

## Gmail SMTP 設定步驟

### 1. 建立 Gmail App Password

1. 登入您的 Google 帳號
2. 前往 [Google 帳戶設定](https://myaccount.google.com/)
3. 點選「安全性」
4. 在「登入 Google」區塊中，點選「應用程式密碼」
5. 選擇「其他（自訂名稱）」，輸入「HK Insurance AML」
6. 複製產生的 16 位應用程式密碼

### 2. 設定環境變數

#### 本地開發環境

在終端機中設定：
```bash
export GMAIL_USER="your-email@gmail.com"
export GMAIL_PASSWORD="your-16-digit-app-password"
```

#### Cloud Run 部署環境

使用 gcloud 指令設定：
```bash
gcloud run services update hk-insurance-aml \
  --set-env-vars GMAIL_USER="your-email@gmail.com",GMAIL_PASSWORD="your-16-digit-app-password" \
  --region asia-east1
```

### 3. 測試 Email 功能

設定完成後，忘記密碼功能將會：
1. 生成隨機密碼
2. 嘗試發送 email 到用戶信箱
3. 如果成功：顯示「新密碼已發送到您的信箱」
4. 如果失敗：顯示新密碼作為備用方案

### 4. 安全注意事項

- 應用程式密碼只會顯示一次，請妥善保存
- 不要將密碼提交到版本控制系統
- 定期更換應用程式密碼
- 考慮使用更安全的 email 服務如 SendGrid

### 5. 替代方案

如不想使用 Gmail，可以：
1. 使用 SendGrid API
2. 使用 AWS SES
3. 使用其他 SMTP 服務

修改 `user_management.py` 中的 `send_password_email()` 函數即可。

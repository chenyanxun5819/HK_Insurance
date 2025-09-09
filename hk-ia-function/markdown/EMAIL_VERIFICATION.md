## 📧 SendGrid Email 驗證指南

### 🎯 API Key 已設置成功！
✅ API Key: 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
✅ Cloud Run 環境變數已更新
✅ 服務已重新部署

### ⚠️ 目前問題：發件人郵箱需要驗證

**現在需要驗證發件人身份：**

1. **登入 SendGrid Dashboard**
   - 前往：https://app.sendgrid.com/
   - 使用您註冊的帳號登入

2. **設置發件人驗證**
   - 點擊左側 "Settings" → "Sender Authentication"
   - 點擊 "Single Sender Verification"
   - 點擊 "Create New Sender"

3. **填寫發件人資訊**
   ```
   From Name: HK Insurance AML System
   From Email: 您的真實郵箱 (例如 astcws@gmail.com)
   Reply To: 同上
   Company: HK Insurance
   Address: (任意有效地址)
   City: Hong Kong
   Country: Hong Kong
   ```

4. **驗證郵箱**
   - 點擊 "Create"
   - 檢查您的郵箱收取驗證郵件
   - 點擊驗證連結

5. **更新發件人郵箱**
   驗證完成後，告訴我您驗證的郵箱，我會更新配置：
   ```bash
   gcloud run services update hk-insurance-aml \
     --region=asia-east1 \
     --update-env-vars SENDGRID_FROM_EMAIL=您驗證的郵箱
   ```

### 🚀 完成後的效果
- ✅ 忘記密碼會發送專業 HTML 郵件
- ✅ 包含新密碼和直接登入連結
- ✅ 專業的系統通知格式

**驗證完發件人郵箱後，告訴我郵箱地址，我會立即更新配置！**

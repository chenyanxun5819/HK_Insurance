# 會員制度設計

## 角色
- **管理員**
- **付費會員**
- **初級會員**

---

## 所有會員基本功能
- 提供註冊（使用 Email 帳號註冊，寄送驗證碼，SendGrid API: `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`）
- 可自行更改密碼  
  **介面連結**：`/account/change-password`
- 可登入  
  **介面連結**：`/login`
- 顯示剩餘可查詢次數
- 忘記密碼功能（系統 Email 發送隨機密碼）  
  **介面連結**：`/account/forgot-password`

---

## 管理員
- 初始帳號：`astcws@hotmail`  
  初始密碼：`admin123`（請直接寫入資料表）
- 設定其他會員的權限（付費或初級會員）
- 設定會員查詢資料筆數限制
- 可無限制查詢資料
- 修改付費會員的查詢筆數
- 搜尋會員（依 email / 名稱）
- 一鍵重置會員查詢次數
- 批量升級 / 降級會員等級
- 管理員後台入口  
  **介面連結**：`/admin/dashboard`

---

## 付費會員
- 有查詢筆數設定欄位
- 付費會員後台入口  
  **介面連結**：`/member/dashboard`

---

## 初級會員
- 可查詢 5 筆資料
- 初級會員後台入口  
  **介面連結**：`/member/dashboard`

---

## 帳號管理與安全（建議補充）
- Email 驗證狀態欄位（避免未驗證帳號直接使用）
- 登入失敗次數限制 / 暫時鎖定（防止暴力破解）
- 最後登入時間 / IP 紀錄（方便管理員稽核異常行為）
- 會員狀態：`active` / `suspended` / `deleted`
- 會員到期日（付費會員用，方便自動降級）
- 建立時間 / 更新時間

---

## 查詢次數管理（建議補充）
- 每日 / 每月重置機制（例如每天 5 次，隔天自動重置）
- 查詢紀錄表（記錄查詢時間、關鍵字、結果數量，方便統計與防濫用）

---

## 預留擴充點（建議補充）
- 付款紀錄表（即使現在不收費，也可以先有結構）
- 通知系統（例如查詢次數快用完時發 Email）

---

## Firestore 資料結構範例
```json
users/{uid} {
  email: "user@example.com",
  role: "admin" | "paid" | "basic",
  status: "active",
  queryLimit: 5,
  queriesUsed: 0,
  createdAt: Timestamp,
  updatedAt: Timestamp,
  lastLoginAt: Timestamp,
  expireAt: Timestamp
}

queryLogs/{logId} {
  uid: "...",
  keyword: "Li Wei",
  resultCount: 3,
  createdAt: Timestamp
}

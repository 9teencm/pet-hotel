# PetHotel Pro 🐾

寵物安親旅館管理系統 — 軟體設計課程專題

## 功能

- 線上住宿預約（含疫苗核檢、防超賣）
- 床位狀態機（有空床 → 已預約 → 住宿中 → 清潔中）
- 美容服務排程（等待中 → 美容中 → 乾燥中 → 已完成 + 飼主通知）
- 晶片號碼查詢寵物
- 角色權限控管（飼主 / 前台 / 美容師 / 保母 / 管理員）
- 管理員使用者 CRUD

## 目錄結構

```
pethotel/
├── backend/
│   ├── app.py            # Flask 應用進入點
│   ├── config.py
│   ├── migrate_db.py     # 一次性資料庫遷移腳本
│   ├── models/           # SQLAlchemy models
│   ├── routes/           # Blueprint 路由
│   ├── services/
│   └── requirements.txt
├── frontend/             # Vue 3 靜態頁面
│   ├── index.html
│   ├── login.html
│   ├── hotelfront.html   # 顧客預約
│   ├── receptionist.html
│   ├── groomer.html
│   ├── nanny.html
│   └── admin.html
└── docs/
    └── state_diagram.puml
```

## 快速啟動

```bash
cd backend
pip install -r requirements.txt
python migrate_db.py   # 首次執行或資料庫升級時
python app.py
```

開啟瀏覽器前往 http://localhost:5000

## 測試帳號

| 角色 | Email | 密碼 |
|------|-------|------|
| 顧客 | customer@test.com | 123456 |
| 美容師 | groomer@test.com | 123456 |
| 保母 | nanny@test.com | 123456 |
| 前台 | reception@test.com | 123456 |
| 管理員 | admin@test.com | 123456 |

## 技術棧

- **後端**：Flask · SQLAlchemy · Flask-JWT-Extended · SQLite
- **前端**：Vue 3 (CDN) · Tailwind CSS (CDN)

# AetherLyric 社群生態倉庫 (AetherLyric Community)

本倉庫為 AetherLyric 官方維護之社群公開節點與外掛生態中心。提供 AetherLyric-app (Android) 與 AetherLyric-server (Python) 動態探索公開伺服器、獲取官方/社群外掛，以及實施安全信任評級。

---

## 一、 目錄結構

```text
AetherLyric-community/
├── data/
│   ├── servers.json                  # 社群公開伺服器節點清單
│   └── plugins.json                  # 社群外掛索引資料庫
├── plugins/
│   ├── json/                         # 宣告式 JSON 歌詞來源外掛
│   │   └── example_source.json       # 官方範例 JSON 歌詞源
│   └── python/                       # 進階 Python 功能外掛
│       └── example_translator/       # 官方範例 Python 歌詞翻譯外掛
│           ├── manifest.json         # 外掛權限與元數據宣告
│           └── main.py               # 外掛實作類別 (translate 方法)
├── scripts/
│   └── scan_plugins.py               # 外掛安全自動化靜態代碼與權限審查工具
├── .github/
│   └── workflows/
│       └── validate.yml              # CI 自動化 JSON 語法檢查與安全排程掃描
├── LICENSE                           # MIT 開源授權條款
├── README.md                         # 倉庫詳細說明文件
└── CONTRIBUTING.md                   # 貢獻指南與安全審核規範
```

---

## 二、 核心資料檔案規範

### 1. 公開伺服器節點 (`data/servers.json`)
提供 App 與 Server 探索公開可用之伺服器。每個節點均具備嚴格的五級信任狀態與節點簽章：
- `name`: 伺服器顯示名稱。
- `url`: 外部可訪問的網址（嚴格禁止內網私有 IP，如 127.0.0.1、192.168.*）。
- `region`: 所在國家/地區代碼（如 TW, HK, JP, US）。
- `description`: 伺服器規格與特徵描述。
- `owner`: 節點擁有者或維護團隊名稱。
- `maintainer_level`: 維護者等級 (`official` | `maintainer` | `contributor`)。
- `trust_status`: 五級信任狀態 (`official` | `verified` | `unverified` | `suspicious` | `banned`)。
- `capabilities`: 支援之功能清單 (`has_ai`, `has_ttml`, `has_ytdlp`)。
- `requires_auth`: 是否需要使用者認證。
- `requires_2fa`: 是否強制要求雙因素驗證 (2FA)。
- `signature`: 節點 HMAC-SHA256 防偽簽章。

### 2. 外掛索引清單 (`data/plugins.json`)
提供雙端擴充商店之索引。包含外掛 ID、分類、作者、下載網址、權限與風險評級：
- `id`: 外掛唯一識別碼。
- `name`: 外掛顯示名稱。
- `category`: 外掛種類 (`lyrics_source` 歌詞源 | `translator` 翻譯引擎 | `system_tool` 系統工具)。
- `author`: 外掛作者名稱。
- `maintainer_level`: 維護者等級 (`official` | `maintainer` | `contributor`)。
- `trust_status`: 五級信任狀態 (`official` | `verified` | `unverified` | `suspicious` | `banned`)。
- `source_url`: 外掛源碼或 JSON 檔案直鏈下載網址。
- `manifest_url`: manifest.json 元數據下載網址（Python 外掛專用）。
- `version`: 外掛語意化版本號（如 1.0.0）。
- `risk_level`: 綜合風險等級 (`low` | `medium` | `high`)。
- `license`: 開源授權條款（統一採用 MIT 授權）。

---

## 三、 五級信任評級系統

為確保使用者裝置與伺服器安全，本社群對所有收錄的節點與外掛實施五級信任等級：

| 等級代碼 | 等級名稱 | 說明與處置機制 |
| :--- | :--- | :--- |
| `official` | 官方推薦 | 由 AetherLyric 核心開發團隊親自維護並簽署，保證最高安全性與可用性。 |
| `verified` | 已驗證節點/外掛 | 通過社群維護者代碼審查與測試驗證之可信來源。 |
| `unverified` | 未驗證節點/外掛 | 社群貢獻者提交之初始節點或外掛，已通過 CI 自動安全掃描，但尚未經人工深入覆核。 |
| `suspicious` | 可疑項目 | 自動掃描發現高危代碼、越權調用、網路頻繁中斷或回報異常之項目。App 與 Server 會顯示醒目警告。 |
| `banned` | 已封禁項目 | 經確認包含惡意行為、後門或重大資安風險之項目。App 啟動時將強制停用並彈窗示警，禁止連線與安裝。 |

---

## 四、 安全防護與自動掃描機制

本倉庫透過 GitHub Actions 排程與 Pull Request 觸發 `scripts/scan_plugins.py`：
1. **高危函數封殺**：嚴禁 Python 外掛調用 `os.system`、`subprocess`、`eval`、`exec`、`__import__` 等系統執行函數。
2. **權限邊界審查**：嚴格比對源碼引用之函式庫是否超出 `manifest.json` 所宣告之權限範圍。
3. **私有網路阻斷**：嚴禁提交包含內部區域網路 IP（127.0.0.1、192.168.x.x、10.x.x.x）之公開節點。
4. **自動降級處置**：若掃描工具發現違規項目，將自動於 `data/plugins.json` 標記為 `suspicious` 並提升風險等級。

---

## 五、 開源授權

本專案所有設定檔案、腳本與範例外掛均採用 [MIT License](LICENSE) 條款授權。
各貢獻者提交之外掛與節點設定亦預設同意以 MIT 條款釋出。

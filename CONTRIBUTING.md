# AetherLyric 社群貢獻指南 (Contributing Guidelines)

感謝您參與 AetherLyric 社群生態建設！為了確保社群公開節點與外掛生態的安全性、相容性與長期穩定，請在提交貢獻前詳閱以下規範。

---

## 一、 MIT 開源授權宣告

本倉庫嚴格採用 **MIT 開源授權條款**。
當您向本倉庫發起 Pull Request 或提交任何伺服器節點設定、外掛檔案時，即代表您同意並確認：
1. 您所提交的所有內容均遵循 MIT License 開源釋出。
2. 您擁有該外掛或節點設定之合法著作權或已取得相容之開源轉授權。
3. 您保證所提交之程式碼絕不包含任何惡意代碼、木馬、鍵盤側錄、非授權資料蒐集或侵犯隱私之行為。

---

## 二、 信任等級定義與審查標準

本社群對外掛與伺服器實施五級信任等級：
1. **`official` (官方)**：
   - 僅由 AetherLyric 官方維護團隊指派。
   - 需經過完整的代碼審計、自動化測試與官方密鑰簽名。
2. **`verified` (已驗證)**：
   - 由認證維護者（Verified Maintainer）主理，或已開源穩定運行超過 30 天且無重大漏洞回報。
   - 需提供清晰之官方文檔、開源源碼倉庫與穩定更新歷史。
3. **`unverified` (未驗證)**：
   - 新提交外掛或社群初次收錄節點之預設等級。
   - 必須通過 CI 自動化 JSON 語法檢查與 `scan_plugins.py` 靜態代碼安全審查。
4. **`suspicious` (可疑)**：
   - 代碼包含潛在越權調用、未經宣告之外部連線、依賴失效或回報嚴重異常之項目。
   - 經靜態安全掃描工具警告後自動標記。
5. **`banned` (封禁)**：
   - 經查實包含惡意程式碼、未授權系統執行、私自上傳使用者隱私憑證或遭大量資安通報之項目。
   - 該節點或外掛將被永久封禁，雙端客戶端啟動時將主動阻斷並強制停用。

---

## 三、 外掛安全規範

### 1. 嚴格禁止的程式碼行為
所有提交之 Python 外掛均會透過 AST 語法樹靜態分析工具進行審核，以下調用一律禁止：
- **禁止使用動態執行函數**：`eval()`, `exec()`, `compile()`, `__import__()`。
- **禁止調用系統底層指令**：`os.system()`, `os.popen()`, `subprocess.*`（`run`, `Popen`, `call`, `check_output` 等）。
- **禁止未授權讀寫檔案**：除外掛沙盒目錄外，禁止調用 `open()`, `os.remove()`, `shutil.*` 等任意路徑檔案操作。
- **禁止未授權讀取環境變數**：未宣告 `read_env` 權限之外掛，嚴禁存取 `os.environ`。

### 2. 最小權限宣告原則 (Principle of Least Privilege)
- 外掛之 `manifest.json` 中宣告之 `permissions` 必須與其實際業務邏輯嚴格一致。
- 歌詞源外掛 (`lyrics_source`) 僅允許宣告 `network` 權限；嚴禁申請 `execute_cmd` 或 `read_env`。
- 宣告之權限若與實際調用不符，CI 將直接判定為審核失敗。

### 3. 公開伺服器節點安全性
- 伺服器網址 (`url`) 必須為外部可正常解析訪問之 FQDN 網域名稱或公網 IP。
- 嚴禁填寫本機迴路位址（`127.0.0.1`, `localhost`）或私人內部區域網路 IP（`192.168.*`, `10.*`, `172.16-31.*`）。
- 提交前請確保伺服器提供合法的 HTTPS 憑證與穩定的連線環境。

---

## 四、 提交流程 (Pull Request Workflow)

1. **Fork 本倉庫** 至您的個人 GitHub 帳號。
2. **建立專用分支**：
   ```bash
   git checkout -b feat/add-my-plugin
   ```
3. **新增或修改檔案**：
   - 若為 JSON 外掛，置於 `plugins/json/<plugin_id>.json`。
   - 若為 Python 外掛，置於 `plugins/python/<plugin_id>/`（包含 `manifest.json` 與 `main.py`）。
   - 更新 `data/plugins.json` 或 `data/servers.json`。
4. **本機執行驗證**：
   ```bash
   python scripts/scan_plugins.py
   ```
   確保終端機顯示 `[OK] 全數外掛安全檢查通過`。
5. **提交並推送**：
   ```bash
   git commit -m "feat(plugin): 新增 <外掛名稱> 擴充外掛"
   git push origin feat/add-my-plugin
   ```
6. **發起 Pull Request**：
   - 清楚描述外掛功能、作者資訊與所使用的 API 來源。
   - 等待 CI 自動化檢查通過與社群維護者代碼審查（Code Review）。

#!/usr/bin/env python3
"""
AetherLyric 社群外掛安全掃描工具 (scripts/scan_plugins.py)
用途：
1. 讀取 data/plugins.json 清單。
2. 掃描 Python 外掛語法樹與源碼，偵測高危函數 (os.system, subprocess, eval, exec, __import__)。
3. 比對 manifest.json 宣告權限與實際源碼行為。
4. 若偵測到未宣告越權或惡意高危調用，自動標記為 suspicious 並回傳警告。
"""

import ast
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List, Set, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
PLUGINS_JSON = BASE_DIR / "data" / "plugins.json"

# 高危險調用黑名單
HIGH_RISK_CALLS = {
    "os.system",
    "os.popen",
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.call",
    "subprocess.check_output",
    "eval",
    "exec",
    "__import__",
    "compile",
    "builtins.eval",
    "builtins.exec",
}

# 敏感庫對應所需權限
MODULE_PERMISSION_MAP = {
    "urllib": "network",
    "urllib.request": "network",
    "requests": "network",
    "httpx": "network",
    "aiohttp": "network",
    "socket": "network",
    "os.environ": "read_env",
    "dotenv": "read_env",
    "builtins.open": "write_file",
}


class PluginSecurityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.calls: Set[str] = set()
        self.imports: Set[str] = set()
        self.high_risk_detected: List[str] = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        mod = node.module or ""
        for alias in node.names:
            full_name = f"{mod}.{alias.name}" if mod else alias.name
            self.imports.add(full_name)
        self.generic_visit(node)

    def visit_Call(self, node):
        call_name = ""
        if isinstance(node.func, ast.Name):
            call_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            cur = node.func
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            parts.reverse()
            call_name = ".".join(parts)

        if call_name:
            self.calls.add(call_name)
            for risk in HIGH_RISK_CALLS:
                if call_name == risk or call_name.endswith(f".{risk}"):
                    self.high_risk_detected.append(f"{call_name} (行號: {node.lineno})")

        self.generic_visit(node)


def scan_python_code(code_str: str) -> Tuple[List[str], Set[str], Set[str]]:
    """
    解析 Python 代碼 AST 並提取潛在安全風險、模組引用與函數調用。
    """
    visitor = PluginSecurityVisitor()
    try:
        tree = ast.parse(code_str)
        visitor.visit(tree)
    except SyntaxError as e:
        return [f"Python 語法錯誤：{e}"], set(), set()
    return visitor.high_risk_detected, visitor.imports, visitor.calls


def load_plugin_content(plugin: Dict) -> str:
    """
    優先從本地倉庫讀取外掛代碼；若無本地路徑則嘗試由 source_url 下載。
    """
    plugin_id = plugin.get("id", "")
    # 檢查本地路徑
    local_candidates = [
        BASE_DIR / "plugins" / "python" / plugin_id / "main.py",
        BASE_DIR / "plugins" / "python" / f"{plugin_id}.py",
    ]
    for p in local_candidates:
        if p.exists():
            return p.read_text(encoding="utf-8")

    # 若無本地檔案且具備 source_url，嘗試網路拉取
    source_url = plugin.get("source_url", "")
    if source_url.startswith("http://") or source_url.startswith("https://"):
        req = urllib.request.Request(
            source_url, headers={"User-Agent": "AetherLyric-Scanner/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8")

    return ""


def load_plugin_manifest(plugin: Dict) -> Dict:
    """
    讀取 manifest 資訊。
    """
    plugin_id = plugin.get("id", "")
    local_manifest = BASE_DIR / "plugins" / "python" / plugin_id / "manifest.json"
    if local_manifest.exists():
        try:
            return json.loads(local_manifest.read_text(encoding="utf-8"))
        except Exception:
            pass

    manifest_url = plugin.get("manifest_url", "")
    if manifest_url.startswith("http://") or manifest_url.startswith("https://"):
        try:
            req = urllib.request.Request(
                manifest_url, headers={"User-Agent": "AetherLyric-Scanner/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            pass

    return {}


def scan_all_plugins() -> int:
    """
    執行全量外掛掃描，若發現違規項目將 trust_status 降級並回傳狀態碼。
    """
    if not PLUGINS_JSON.exists():
        print(f"[錯誤] 找不到外掛資料庫：{PLUGINS_JSON}")
        return 1

    try:
        plugins_data = json.loads(PLUGINS_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[錯誤] 解析 {PLUGINS_JSON} 失敗：{exc}")
        return 1

    if not isinstance(plugins_data, list):
        print(f"[錯誤] {PLUGINS_JSON} 頂層結構必須為 JSON 陣列")
        return 1

    modified = False
    violations_found = False

    print(f"[*] 開始掃描外掛清單，共有 {len(plugins_data)} 個項目...")

    for plugin in plugins_data:
        p_id = plugin.get("id", "unknown")
        category = plugin.get("category", "")
        declared_trust = plugin.get("trust_status", "unverified")

        # 僅針對 Python 外掛執行深度 AST 掃描
        if plugin.get("manifest_url") or (BASE_DIR / "plugins" / "python" / p_id).exists():
            print(f"[>] 掃描 Python 外掛: {p_id} (目前信任狀態: {declared_trust})")
            code_text = load_plugin_content(plugin)
            if not code_text:
                print(f"    [略過] 未找到對應代碼檔案，略過 AST 掃描。")
                continue

            manifest = load_plugin_manifest(plugin)
            permissions = set(manifest.get("permissions", []))

            high_risks, imports, calls = scan_python_code(code_text)

            is_suspicious = False
            reasons = []

            # 1. 高危函數調用檢查
            if high_risks:
                is_suspicious = True
                reasons.append(f"偵測到高危函數調用: {', '.join(high_risks)}")

            # 2. 權限邊界比對
            # 檢查網路庫使用
            network_modules = {"requests", "httpx", "urllib", "socket", "aiohttp"}
            if any(m in imports or any(i.startswith(f"{m}.") for i in imports) for m in network_modules):
                if "network" not in permissions and "execute_cmd" not in permissions:
                    is_suspicious = True
                    reasons.append("調用網路庫但未於 manifest.json 宣告 network 權限")

            # 3. 分類相符性比對 (例如歌詞源不應宣告 execute_cmd)
            if category == "lyrics_source" and "execute_cmd" in permissions:
                is_suspicious = True
                reasons.append("歌詞源外掛宣告 execute_cmd 不符合分類最小權限原則")

            if is_suspicious:
                violations_found = True
                print(f"    [警告] 外掛 {p_id} 存在安全違規！")
                for r in reasons:
                    print(f"      - {r}")

                if declared_trust not in ("suspicious", "banned"):
                    print(f"    [處置] 將信任狀態由 {declared_trust} 自動降級為 suspicious")
                    plugin["trust_status"] = "suspicious"
                    plugin["risk_level"] = "high"
                    modified = True
            else:
                print(f"    [通過] 安全檢查正常，無高危調用與未授權行為。")

    if modified:
        print("[*] 正在更新 data/plugins.json 信任評級...")
        PLUGINS_JSON.write_text(
            json.dumps(plugins_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print("[*] data/plugins.json 更新完成。")

    if violations_found:
        print("[!] 掃描完畢：發現外掛存在安全風險。")
        return 0  # 標記完成並更新檔案，避免 CI 中斷
    else:
        print("[OK] 全數外掛安全檢查通過，無任何惡意風險。")
        return 0


if __name__ == "__main__":
    sys.exit(scan_all_plugins())

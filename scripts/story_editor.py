#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ピンク髪の魔法使い ─ 編集者役 (GitHub Actions版・urllibのみ)

各話生成後に呼ばれ、世界観固定値・既出キャラ・現在状態と
今回の話文を照合して矛盾を検出する。

重大度の方針:
- high   : 物語が破綻するレベル → Discord 通知 + ログ記録
- medium : 読者が気になるレベル → ログ記録のみ
- low    : 些細・主観的           → ログ記録のみ
"""
import os
import json
import re
import urllib.request
import urllib.error
from datetime import datetime

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDITOR_LOG_FILE = os.path.join(REPO_DIR, "editor_log.json")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"


def _call_claude(api_key, prompt, max_tokens=1500):
    body = json.dumps({
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")
    req = urllib.request.Request(CLAUDE_API_URL, data=body, method="POST")
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("content-type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["content"][0]["text"].strip()
    except Exception as e:
        print(f"[WARN] claude call failed: {e}")
        return ""


def _format_facts(facts):
    return "\n".join([f"- {f['fact']}" for f in facts]) if facts else "（なし）"

def _format_chars(chars):
    if not chars: return "（なし）"
    return "\n".join([f"- {c['name']}（{c.get('role', '')}）：{c.get('description', '')}" for c in chars])

def _format_locs(locs):
    if not locs: return "（なし）"
    return "\n".join([f"- {l['name']}：{l.get('description', '')}" for l in locs])

def _format_state(state):
    if not state: return "（なし）"
    return (
        f"- Day {state.get('in_story_day', '?')}\n"
        f"- 場所：{state.get('location', '')}\n"
        f"- ロゼリア状況：{state.get('roselia_status', '')}\n"
        f"- 同行者：{state.get('companion', '')}"
    )

def _format_events(events):
    if not events: return "（なし）"
    return "\n".join([f"- {e['event']}：あと{e.get('remaining_days', '?')}日（Day {e.get('due_in_story_day', '?')}）" for e in events])


def check_episode(api_key, episode_num, story_text, prev_context):
    """話文と context を比較して矛盾を検出。"""
    facts_block  = _format_facts(prev_context.get("setting_facts", []))
    chars_block  = _format_chars(prev_context.get("key_characters", []))
    locs_block   = _format_locs(prev_context.get("key_locations", []))
    state_block  = _format_state(prev_context.get("current_state"))
    events_block = _format_events(prev_context.get("pending_events", []))
    prev_summary = prev_context.get("last_episode_summary", "（なし）")

    prompt = f"""あなたは厳しいファンタジー小説の編集者です。
作家が書いた最新話に **物語を破綻させる重大な矛盾** がないかチェックしてください。

【世界観の固定値（絶対に変更不可）】
{facts_block}

【既出登場人物（名前・特徴は不変）】
{chars_block}

【既出地名・組織】
{locs_block}

【話の冒頭時点の状況】
{state_block}

【迫っている出来事（残り日数）】
{events_block}

【前話までのあらすじ】
{prev_summary}

─────────────────────────────
【今回の第{episode_num}話 本文】
{story_text}
─────────────────────────────

タスク：上記との矛盾を検出してください。

【重大度の判定基準】
- high   : 物語破綻級。例：日数の矛盾、人物の同一性が崩れる、別れた人物が突然居る、世界観の数値違反、プロット巻き戻り
- medium : 気になるレベル。例：キャラの細かい設定変更、地名の表記揺れ、能力の説明変更
- low    : 些細。例：文体の揺れなど（基本的に出さなくてよい）

【厳格なルール】
- 文体や表現の好みは指摘しない
- 「読者が混乱する事実関係の矛盾」のみ指摘
- 矛盾がなければ必ず空配列 [] を返す
- 推測・憶測の指摘は避ける（明確に矛盾していること）

【出力形式】（JSON配列のみ・説明文なし）
[
  {{"severity": "high", "category": "timeline / character / location / world / plot", "issue": "具体的な矛盾の内容と、どの既存事実と矛盾するか"}}
]
"""
    text = _call_claude(api_key, prompt, max_tokens=1500)
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return []


def log_issues(episode_num, issues):
    entry = {
        "episode": episode_num,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "issues": issues,
        "summary": {
            "high":   sum(1 for i in issues if i.get("severity") == "high"),
            "medium": sum(1 for i in issues if i.get("severity") == "medium"),
            "low":    sum(1 for i in issues if i.get("severity") == "low"),
        }
    }
    log = []
    if os.path.exists(EDITOR_LOG_FILE):
        try:
            with open(EDITOR_LOG_FILE, encoding="utf-8") as f:
                log = json.load(f)
        except Exception:
            log = []
    log.append(entry)
    with open(EDITOR_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def notify_if_high(episode_num, issues):
    high = [i for i in issues if i.get("severity") == "high"]
    if not high:
        return False
    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "")
    if not webhook:
        return False
    lines = [f"⚠️ 第{episode_num}話に **{len(high)}件の重大な矛盾** を検出"]
    for i in high[:5]:
        lines.append(f"・[{i.get('category', '?')}] {i.get('issue', '')[:200]}")
    msg = "\n".join(lines)
    try:
        data = json.dumps({"content": msg}).encode("utf-8")
        req = urllib.request.Request(webhook, data=data,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        print(f"[WARN] discord notify failed: {e}")
        return False


def run_editor(api_key, episode_num, story_text, prev_context):
    print(f"[*] Editor checking episode {episode_num}...")
    issues = check_episode(api_key, episode_num, story_text, prev_context)
    if not issues:
        print("[OK] No issues found")
        log_issues(episode_num, [])
        return
    summary = {
        "high":   sum(1 for i in issues if i.get("severity") == "high"),
        "medium": sum(1 for i in issues if i.get("severity") == "medium"),
        "low":    sum(1 for i in issues if i.get("severity") == "low"),
    }
    print(f"[INFO] Issues: high={summary['high']}, medium={summary['medium']}, low={summary['low']}")
    log_issues(episode_num, issues)
    if summary["high"] > 0:
        notify_if_high(episode_num, issues)
        print(f"[ALERT] {summary['high']} HIGH severity issue(s) -> Discord notified")

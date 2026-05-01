#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions で毎日22:00(JST)に実行される自動生成スクリプト。
ストーリー生成 → 画像生成 → HTML変換 → context更新 を一括実行。
"""
import os
import sys
import json
import re
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

# ========== パス設定（リポジトリルート基準）==========
REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE   = os.path.join(REPO_DIR, "story_config.json")
CONTEXT_FILE  = os.path.join(REPO_DIR, "story_context.json")
STORIES_DIR   = os.path.join(REPO_DIR, "stories")
IMAGES_DIR    = os.path.join(REPO_DIR, "stories", "images")

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1024&height=576&model=flux&nologo=true&enhance=true&seed={seed}"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"


def call_claude(api_key, prompt, max_tokens=3000):
    """anthropicパッケージ不要・urllibで直接Anthropic APIを呼ぶ"""
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
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body}")

# ========== HTML テンプレート ==========
HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>第{episode_num}話 ─ ピンク髪の魔法使い</title>
    <meta name="description" content="ピンク髪の魔法使いロゼリアの物語、第{episode_num}話。">
    <meta property="og:title" content="第{episode_num}話 ─ ピンク髪の魔法使い">
    <meta property="og:description" content="ピンク髪の魔法使いロゼリアの物語、第{episode_num}話。">
    <meta property="og:type" content="article">
    <meta property="og:image" content="https://k6529y.github.io/story-pink-wizard/stories/images/{episode_num:03d}.jpg">
    <meta property="og:locale" content="ja_JP">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="icon" href="../favicon.svg" type="image/svg+xml">
    <link rel="stylesheet" href="../css/story.css">
</head>
<body>

<div class="reading-progress" id="readingProgress"></div>

<header class="site-header">
    <div class="brand">
        <a href="../index.html" class="brand-link">
            <span class="brand-mark" aria-hidden="true">
                <svg viewBox="0 0 32 32" width="22" height="22">
                    <circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" stroke-width="0.8" opacity="0.7"/>
                    <circle cx="16" cy="16" r="10" fill="none" stroke="currentColor" stroke-width="0.4" stroke-dasharray="1 1" opacity="0.6"/>
                    <path d="M16 9.5 L17.5 14 L22 14.3 L18.5 17 L19.6 21.5 L16 19 L12.4 21.5 L13.5 17 L10 14.3 L14.5 14 Z" fill="currentColor"/>
                </svg>
            </span>
            <span class="brand-text">ピンク髪の<span class="accent">魔法使い</span></span>
        </a>
        <span class="ep-num">第 {episode_num} 話</span>
    </div>
</header>

{chapter_banner}{image_block}
<article class="episode-body fade-in">
    <div class="episode-meta">
        <div class="ep-label">{episode_chapter_label}</div>
        <h1>{episode_title}</h1>
    </div>
    <div class="story-content">
{story_body}
    </div>
</article>

<div class="share-bar">
    <span class="label">この話を共有</span>
    <a href="https://twitter.com/intent/tweet?text={share_text}&url={share_url}" target="_blank" rel="noopener">𝕏 でポスト</a>
    <a href="javascript:navigator.clipboard.writeText('{share_url}').then(()=>this.textContent='✓ コピー済み');">🔗 リンクをコピー</a>
</div>

<nav class="episode-nav">
{prev_nav}
{next_nav}
</nav>

<footer class="site-footer">
    <p>ピンク髪の魔法使い ─ Pink-Haired Wizard</p>
    <p>毎日 廿二時 更新 ─ Powered by <a href="https://claude.com" target="_blank" rel="noopener">Claude</a> + GitHub Pages</p>
</footer>

<script src="../scripts/story.js"></script>
</body>
</html>
"""

KANJI_CHAPTERS = ['第一章', '第二章', '第三章', '第四章', '第五章',
                  '第六章', '第七章', '第八章', '第九章', '第十章']

# ========== ユーティリティ ==========

def load_json(filepath):
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def send_discord(message):
    if not WEBHOOK_URL:
        print("[*] Discord webhook not configured (skip)")
        return False
    try:
        data = json.dumps({"content": message}).encode("utf-8")
        req = urllib.request.Request(
            WEBHOOK_URL, data=data,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        print(f"[WARN] Discord: {e}")
        return False

# ========== ストーリー生成 ==========

def get_current_arc(config, episode_num):
    for arc in config.get("story_arcs", []):
        if arc["episodes"][0] <= episode_num <= arc["episodes"][1]:
            return arc
    return None

def generate_story(api_key, config, context, episode_num):
    arc = get_current_arc(config, episode_num)
    prompt = f"""あなたは「ピンク髪の魔法使い」というファンタジー小説の執筆者です。

【主人公の設定】
名前: {config["hero"]["name"]}
年齢: {config["hero"]["age"]}
外見: {config["hero"]["appearance"]}
性格: {config["hero"]["personality"]}
背景: {config["hero"]["background"]}
能力: {config["hero"]["magic_abilities"]}

【世界観】
舞台: {config["world"]["setting"]}
魔法体系: {config["world"]["magic_system"]}

【現在の章】
タイトル: {arc["title"]}
テーマ: {", ".join(arc["themes"])}

【前話までの流れ】
{context.get("last_episode_summary", "プロローグ")}

【タスク】
第{episode_num}話を執筆してください。要件：
- 文字数: 2000字前後
- 形式: Markdown（本文のみ、見出しなし）
- スタイル: 引き込まれる執筆。キャラの感情・成長を丁寧に描写
- 内容: 冒険・魔法・日常のバランス。終わり方は「次話への続き」を意識
- セリフ: 自然で個性的に

本文のみ返してください（説明は不要）。"""

    return call_claude(api_key, prompt, max_tokens=3000)

def generate_summary(api_key, story_text, episode_num):
    prompt = f"""以下の小説第{episode_num}話を3〜4行で簡潔にまとめてください。
次話執筆時の「前話の内容」として使います。重要な出来事・感情・伏線を含めてください。

---
{story_text[:1000]}...
---

サマリー:"""
    return call_claude(api_key, prompt, max_tokens=300)

# ========== 画像生成 ==========

def generate_image_prompt(api_key, story_text, episode_num):
    prompt = f"""Based on this Japanese fantasy novel excerpt (Episode {episode_num}), write ONE English image generation prompt for the most visually striking scene.

Requirements:
- English only, 50-70 words
- Include style: "anime fantasy illustration, soft pastel colors, cinematic lighting, high quality, detailed"
- Main character when present: "teenage girl with long pink hair and emerald green eyes, glowing magical mark on left forearm, traveler's cloak"
- Focus on atmosphere and emotion
- No violence or inappropriate content
- Return prompt text ONLY

Novel excerpt:
{story_text[:600]}"""

    return call_claude(api_key, prompt, max_tokens=200)

def download_image(prompt, save_path, episode_num):
    encoded = urllib.parse.quote(prompt)
    url = POLLINATIONS_URL.format(prompt=encoded, seed=episode_num * 42)
    print(f"[*] Generating image...")
    print(f"    {prompt[:80]}...")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            content = resp.read()
        if len(content) < 1000:
            print(f"[WARN] Image too small ({len(content)}B)")
            return False
        with open(save_path, "wb") as f:
            f.write(content)
        print(f"[OK] Image: {len(content):,} bytes")
        return True
    except Exception as e:
        print(f"[WARN] Image failed: {e}")
        return False

# ========== HTML変換 ==========

def md_to_html_body(md_text):
    lines = md_text.split('\n')
    parts = []
    para = []

    def flush():
        if para:
            text = ' '.join(para).strip()
            if text:
                parts.append(f'        <p>{text}</p>')
            para.clear()

    for line in lines:
        s = line.strip()
        if s.startswith('#'):
            flush(); continue
        if s in ('---', '***', '___'):
            flush()
            parts.append('        <hr/>')
            continue
        if s == '':
            flush(); continue
        s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
        para.append(s)

    flush()
    return '\n'.join(parts)

def get_chapter_info(config, episode_num):
    """story_config.json から章情報を取得"""
    for idx, arc in enumerate(config.get("story_arcs", [])):
        ep_range = arc.get("episodes", [0, 0])
        if ep_range[0] <= episode_num <= ep_range[1]:
            title = arc.get("title", "")
            clean = re.sub(r'^第[一二三四五六七八九十0-9]+章[：:]\s*', '', title)
            return {
                "kanji_num": KANJI_CHAPTERS[idx] if idx < len(KANJI_CHAPTERS) else f"第{idx+1}章",
                "name": clean,
                "episodes": ep_range,
                "is_first": episode_num == ep_range[0],
            }
    return None


def make_chapter_banner(config, episode_num):
    info = get_chapter_info(config, episode_num)
    if not info or not info["is_first"]:
        return ""
    return (
        f'<section class="chapter-banner fade-in">\n'
        f'    <div class="ornament">✦ ✦ ✦</div>\n'
        f'    <div class="chap-num">{info["kanji_num"]}</div>\n'
        f'    <div class="chap-name">{info["name"]}</div>\n'
        f'</section>\n'
    )


def build_html(story_text, episode_num, total_episodes, has_image, config=None):
    body = md_to_html_body(story_text)

    if has_image:
        image_block = (
            f'<section class="episode-hero fade-in">\n'
            f'    <div class="frame">\n'
            f'        <img src="images/{episode_num:03d}.jpg" alt="第{episode_num}話のシーン">\n'
            f'    </div>\n'
            f'    <p class="image-credit">挿絵 ─ Pollinations.ai / FLUX</p>\n'
            f'</section>\n'
        )
    else:
        image_block = ''

    chapter_banner = make_chapter_banner(config, episode_num) if config else ''
    chap = get_chapter_info(config, episode_num) if config else None
    episode_title = f"第{episode_num}話"
    if chap:
        episode_chapter_label = f'{chap["kanji_num"]} ─ {chap["name"]}'
    else:
        episode_chapter_label = ""

    prev_nav = (f'    <a href="{episode_num-1:03d}.html" class="prev">← 第{episode_num-1}話</a>'
                if episode_num > 1 else
                '    <a href="../index.html" class="prev">← 目次に戻る</a>')
    next_nav = (f'    <a href="{episode_num+1:03d}.html" class="next">第{episode_num+1}話 →</a>'
                if episode_num < total_episodes else
                '    <span class="disabled">最新話</span>')

    share_url = f"https://k6529y.github.io/story-pink-wizard/stories/{episode_num:03d}.html"
    share_text = urllib.parse.quote(f"第{episode_num}話 ─ ピンク髪の魔法使い")

    return HTML_TEMPLATE.format(
        episode_num=episode_num,
        episode_title=episode_title,
        episode_chapter_label=episode_chapter_label,
        image_block=image_block,
        chapter_banner=chapter_banner,
        story_body=body,
        prev_nav=prev_nav,
        next_nav=next_nav,
        share_text=share_text,
        share_url=share_url,
    )

# ========== index.json更新 ==========

def update_index(episode_num, today_str, has_image):
    index_file = os.path.join(STORIES_DIR, "index.json")
    data = {"episodes": [], "total": 0, "last_updated": ""}
    if os.path.exists(index_file):
        data = load_json(index_file)

    existing = [e["number"] for e in data.get("episodes", [])]
    if episode_num not in existing:
        data["episodes"].append({
            "number": episode_num,
            "file": f"{episode_num:03d}.html",
            "title": f"第{episode_num}話",
            "published": today_str,
            "has_image": has_image
        })
        data["total"] = len(data["episodes"])
        data["last_updated"] = today_str
        save_json(index_file, data)
    return data["total"]

# ========== メイン ==========

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("[ERROR] ANTHROPIC_API_KEY not set")
        sys.exit(1)

    config = load_json(CONFIG_FILE)
    context = load_json(CONTEXT_FILE)
    episode_num = context.get("last_episode", 0) + 1
    arc = get_current_arc(config, episode_num)

    if not arc:
        print(f"[ERROR] Episode {episode_num} out of range")
        sys.exit(1)

    print(f"[*] Episode {episode_num} / {arc['title']}")
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. ストーリー生成
    print("[*] Generating story...")
    story_text = generate_story(api_key, config, context, episode_num)
    print(f"[OK] {len(story_text)} chars")

    # 2. 画像生成
    image_path = os.path.join(IMAGES_DIR, f"{episode_num:03d}.jpg")
    has_image = False
    try:
        img_prompt = generate_image_prompt(api_key, story_text, episode_num)
        has_image = download_image(img_prompt, image_path, episode_num)
    except Exception as e:
        print(f"[WARN] Image skipped: {e}")

    # 3. HTML変換・保存
    os.makedirs(STORIES_DIR, exist_ok=True)
    total = update_index(episode_num, today, has_image)
    html = build_html(story_text, episode_num, total, has_image, config=config)
    html_path = os.path.join(STORIES_DIR, f"{episode_num:03d}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] HTML saved: {html_path}")

    # 4. サマリー生成・context更新
    print("[*] Generating summary...")
    summary = generate_summary(api_key, story_text, episode_num)
    context["last_episode"] = episode_num
    context["last_episode_summary"] = summary
    save_json(CONTEXT_FILE, context)
    print("[OK] context updated")

    # 5. Discord通知
    send_discord(
        f"[NEW] 第{episode_num}話 公開！\n"
        f"{arc['title']}\n"
        f"https://k6529y.github.io/story-pink-wizard/stories/{episode_num:03d}.html"
    )

    print(f"[OK] Episode {episode_num} done")

if __name__ == "__main__":
    main()

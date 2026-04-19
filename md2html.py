#!/usr/bin/env python3
"""
AI 日报 — 多页面 HTML 生成器 v2
支持深色模式、动画卡片、沉浸式阅读体验
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import markdown
    from markdown.extensions.codehilite import CodeHiliteExtension
    from markdown.extensions.tables import TableExtension
    from markdown.extensions.fenced_code import FencedCodeExtension
except ImportError:
    print("❌ 缺少依赖，请先安装：pip install markdown")
    sys.exit(1)


CSS = """
:root {
    --bg: #f8f7f4;
    --bg-card: #ffffff;
    --text: #1a1a1a;
    --text-muted: #6b7280;
    --accent: #2563eb;
    --accent-soft: #dbeafe;
    --accent-glow: rgba(37,99,235,0.12);
    --accent2: #7c3aed;
    --accent2-soft: #ede9fe;
    --border: #e5e7eb;
    --code-bg: #f1f0ed;
    --heading: #0f172a;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
    --shadow: 0 4px 20px rgba(0,0,0,0.08);
    --shadow-lg: 0 12px 40px rgba(0,0,0,0.12);
    --radius: 16px;
    --radius-sm: 10px;
    --font: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
    :root {
        --bg: #0c0c0f;
        --bg-card: #16161a;
        --text: #e2e8f0;
        --text-muted: #94a3b8;
        --accent: #60a5fa;
        --accent-soft: #1e3a5f;
        --accent-glow: rgba(96,165,250,0.15);
        --accent2: #a78bfa;
        --accent2-soft: #2e1f5e;
        --border: #2a2a35;
        --code-bg: #1e1e26;
        --heading: #f1f5f9;
    }
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: var(--font);
    background: var(--bg);
    color: var(--text);
    line-height: 1.8;
    min-height: 100vh;
}

/* ── 通用容器 ── */
.container {
    max-width: 860px;
    margin: 0 auto;
    padding: 2rem 1.5rem 5rem;
}

/* ── 首页 Hero ── */
.home-hero {
    text-align: center;
    padding: 5rem 1.5rem 4rem;
    position: relative;
}
.home-hero::before {
    content: '';
    position: absolute;
    top: 0; left: 50%; transform: translateX(-50%);
    width: 600px; height: 400px;
    background: radial-gradient(ellipse, var(--accent-glow) 0%, transparent 70%);
    pointer-events: none;
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--accent-soft);
    color: var(--accent);
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 6px 14px;
    border-radius: 999px;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(37,99,235,0.2);
}
.home-hero h1 {
    font-size: clamp(2rem, 5vw, 3rem);
    font-weight: 900;
    color: var(--heading);
    line-height: 1.15;
    letter-spacing: -0.03em;
    margin-bottom: 0.75rem;
}
.home-hero .subtitle {
    color: var(--text-muted);
    font-size: 1.05rem;
    margin-bottom: 0.5rem;
}
.home-hero .date-tag {
    font-size: 0.85rem;
    color: var(--accent);
    font-weight: 600;
}

/* ── 分割线 ── */
.divider {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 2.5rem 0;
    color: var(--text-muted);
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.divider::before, .divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ── 板块卡片网格 ── */
.toc-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 1.25rem;
    margin-top: 1rem;
}
.toc-card {
    display: flex;
    flex-direction: column;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.75rem;
    text-decoration: none;
    color: inherit;
    transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1),
                box-shadow 0.2s ease,
                border-color 0.2s ease;
    box-shadow: var(--shadow-sm);
    position: relative;
    overflow: hidden;
}
.toc-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    opacity: 0;
    transition: opacity 0.2s;
}
.toc-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
    border-color: var(--accent);
    text-decoration: none;
    color: inherit;
}
.toc-card:hover::before { opacity: 1; }

.card-icon {
    width: 44px; height: 44px;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem;
    margin-bottom: 1rem;
    background: var(--accent-soft);
}
.card-num {
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.3rem;
}
.card-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--heading);
    margin-bottom: 0.4rem;
    line-height: 1.3;
}
.card-desc {
    font-size: 0.82rem;
    color: var(--text-muted);
    line-height: 1.5;
    flex: 1;
}
.card-arrow {
    margin-top: 1rem;
    font-size: 0.8rem;
    color: var(--accent);
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 4px;
}

/* ── 板块页 Header ── */
.section-hero {
    padding: 3.5rem 0 2.5rem;
    position: relative;
}
.section-hero::before {
    content: '';
    position: absolute;
    top: 0; left: -1.5rem; right: -1.5rem; bottom: 0;
    background: linear-gradient(135deg, var(--accent-glow) 0%, transparent 60%);
    border-radius: 0 0 var(--radius) var(--radius);
    z-index: -1;
}
.breadcrumb {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.82rem;
    color: var(--text-muted);
    margin-bottom: 1rem;
    font-weight: 500;
}
.breadcrumb a { color: var(--accent); text-decoration: none; font-weight: 600; }
.breadcrumb a:hover { text-decoration: underline; }
.section-title-wrap { display: flex; align-items: flex-start; gap: 1rem; }
.section-icon {
    width: 56px; height: 56px;
    border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.8rem;
    background: var(--bg-card);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
    flex-shrink: 0;
}
.section-title-wrap h1 {
    font-size: clamp(1.5rem, 4vw, 2.2rem);
    font-weight: 900;
    color: var(--heading);
    line-height: 1.2;
    letter-spacing: -0.02em;
    padding-top: 0.4rem;
}
.section-meta {
    display: flex;
    gap: 1.5rem;
    margin-top: 0.75rem;
    flex-wrap: wrap;
}
.meta-item {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 0.82rem;
    color: var(--text-muted);
}
.meta-item .dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent);
}

/* ── 内容块 ── */
.content-section {
    margin-bottom: 3rem;
}
.section-label {
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ── 项目卡片 ── */
.item-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.75rem;
    margin-bottom: 1.25rem;
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.2s, border-color 0.2s;
}
.item-card:hover {
    box-shadow: var(--shadow);
    border-color: rgba(37,99,235,0.3);
}
.item-card h3 {
    font-size: 1.1rem;
    font-weight: 800;
    color: var(--heading);
    margin-bottom: 0.25rem;
    letter-spacing: -0.01em;
}
.item-card .item-subtitle {
    font-size: 0.8rem;
    color: var(--accent);
    font-weight: 600;
    margin-bottom: 1rem;
}
.item-card .one-liner {
    font-size: 0.9rem;
    color: var(--text);
    background: var(--code-bg);
    border-left: 3px solid var(--accent);
    padding: 0.5rem 1rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: 1rem;
    font-weight: 500;
}

.meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
}
.tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: var(--accent-soft);
    color: var(--accent);
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 999px;
    letter-spacing: 0.03em;
}
.tag.star { background: #fef3c7; color: #d97706; }
.tag.new { background: #d1fae5; color: #059669; }

.field-label {
    font-size: 0.72rem;
    font-weight: 800;
    color: var(--accent2);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 1rem;
    margin-bottom: 0.3rem;
}
.field-label:first-child { margin-top: 0; }

p { margin-bottom: 0.75rem; }
ul { padding-left: 1.25rem; margin-bottom: 0.75rem; }
li { margin-bottom: 0.25rem; }

a { color: var(--accent); }
a:hover { text-decoration: underline; }

code {
    font-family: "SF Mono", "Fira Code", Consolas, monospace;
    font-size: 0.8em;
    background: var(--code-bg);
    padding: 0.15em 0.4em;
    border-radius: 5px;
    color: #c7254e;
    border: 1px solid var(--border);
}
@media (prefers-color-scheme: dark) { code { color: #f78c6c; } }

pre {
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    overflow-x: auto;
    margin: 1rem 0;
}
pre code { background: none; padding: 0; color: var(--text); font-size: 0.82rem; border: none; }

table { width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.875rem; border-radius: 10px; overflow: hidden; }
th, td { border: 1px solid var(--border); padding: 0.6rem 0.9rem; text-align: left; }
th { background: var(--code-bg); font-weight: 700; font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
tr:nth-child(even) td { background: rgba(0,0,0,0.02); }
@media (prefers-color-scheme: dark) { tr:nth-child(even) td { background: rgba(255,255,255,0.03); } }

hr { border: none; border-top: 1px solid var(--border); margin: 2.5rem 0; }

/* ── 页脚导航 ── */
.page-footer {
    border-top: 1px solid var(--border);
    padding-top: 2rem;
    margin-top: 3rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}
.footer-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.875rem;
    color: var(--text-muted);
    text-decoration: none;
    font-weight: 500;
    padding: 8px 16px;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--bg-card);
    transition: all 0.2s;
}
.footer-link:hover {
    color: var(--accent);
    border-color: var(--accent);
    background: var(--accent-soft);
    text-decoration: none;
}
.footer-link.primary {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
}
.footer-link.primary:hover {
    background: #1d4ed8;
    color: #fff;
}

/* ── 来源信息 ── */
.source-block {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.75rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-sm);
}
.source-block h3 {
    font-size: 1.05rem;
    font-weight: 800;
    color: var(--heading);
    margin-bottom: 0.25rem;
}
.source-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 1rem;
    font-size: 0.78rem;
    color: var(--text-muted);
}

/* ── 滚动条 ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ── 动画 ── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
.home-hero, .toc-card, .item-card, .source-block { animation: fadeInUp 0.5s ease both; }
.toc-card:nth-child(1) { animation-delay: 0.05s; }
.toc-card:nth-child(2) { animation-delay: 0.1s; }
.toc-card:nth-child(3) { animation-delay: 0.15s; }
.toc-card:nth-child(4) { animation-delay: 0.2s; }
.toc-card:nth-child(5) { animation-delay: 0.25s; }
.toc-card:nth-child(6) { animation-delay: 0.3s; }
"""

SECTION_ICONS = {
    1: "🚀",
    2: "📖",
    3: "📢",
    4: "⚡",
    5: "🇨🇳",
    6: "💡",
}

SECTION_DESCS = {
    1: "GitHub 小众爆款 · 6个近期增速最快的开源工具",
    2: "BestBlogs 高分精选 · 3篇高质量技术评论",
    3: "官方博客新动态 · 3条官方重大发布",
    4: "开源工具 & 模型更新 · 3个重磅更新",
    5: "国内技术圈 · 3条国内 AI 动态",
    6: "板块洞察 · 1篇深度分析",
}


def parse_sections(md_content):
    lines = md_content.split("\n")
    sections = []
    current_title = ""
    current_lines = []
    for line in lines:
        if re.match(r"^##\s+", line):
            if current_title:
                sections.append((current_title, "\n".join(current_lines)))
            current_title = re.sub(r"^##\s+", "", line).strip()
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_title and current_lines:
        sections.append((current_title, "\n".join(current_lines)))
    return sections


def md_to_html_body(md_text):
    md = markdown.Markdown(
        extensions=[
            FencedCodeExtension(),
            CodeHiliteExtension(css_class="highlight", guess_lang=False),
            TableExtension(),
        ],
        output_format="html",
    )
    html = md.convert(md_text)
    # 裸 URL → 可点击链接
    html = re.sub(
        r"(?<!href=\"(?<!src=\")(?<!=\"))(https?://[^\s<>\"\'\) ]+)",
        r'<a href="\1" target="_blank" rel="noopener">\1</a>',
        html,
    )
    return html


def make_page(title, body_content):
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<meta name="description" content="AI技术情报日报，每日追踪AI开源项目与技术动态">\n'
        "<title>" + title + "</title>\n"
        "<style>\n" + CSS + "\n</style>\n"
        "</head>\n"
        "<body>\n" + body_content + "\n</body>\n"
        "</html>"
    )


def generate_pages(md_path, output_dir=None):
    md_path = Path(md_path)
    if not md_path.exists():
        print(f"❌ 文件不存在: {md_path}")
        return False

    content = md_path.read_text(encoding="utf-8")

    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    page_title = title_match.group(1).strip() if title_match else md_path.stem
    date_match = re.search(r"(\d{4}年\d{1,2}月\d{1,2}日)", content)
    date_str = date_match.group(1) if date_match else ""

    out_dir = Path(output_dir) if output_dir else md_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    sections = parse_sections(content)
    total = len(sections)

    # ── index.html ──────────────────────────────
    cards = []
    for i, (sec_title, _) in enumerate(sections, 1):
        icon = SECTION_ICONS.get(i, "📄")
        desc = SECTION_DESCS.get(i, "")
        card = (
            f'<a class="toc-card" href="section-{i}.html">\n'
            f'    <div class="card-icon">{icon}</div>\n'
            f'    <div class="card-num">板块 {i}</div>\n'
            f'    <div class="card-title">{sec_title}</div>\n'
            f'    <div class="card-desc">{desc}</div>\n'
            f'    <div class="card-arrow">阅读全文 →</div>\n'
            f'</a>'
        )
        cards.append(card)

    index_body = (
        '<div class="container">\n'
        '    <div class="home-hero">\n'
        '        <div class="hero-badge">⚡ 每日更新</div>\n'
        f'        <h1>{page_title}</h1>\n'
        f'        <div class="subtitle">AI 技术情报 · 近24小时</div>\n'
        f'        <div class="date-tag">📅 {date_str}</div>\n'
        '    </div>\n'
        '    <div class="divider">选择板块</div>\n'
        '    <div class="toc-grid">\n' + "\n".join(cards) + '\n'
        '    </div>\n'
        '</div>'
    )

    (out_dir / "index.html").write_text(make_page(page_title, index_body), encoding="utf-8")
    print(f"  ✅ index.html")

    # ── section-N.html ──────────────────────────
    for i, (sec_title, sec_md) in enumerate(sections, 1):
        icon = SECTION_ICONS.get(i, "📄")
        prev_link = (
            f'    <a class="footer-link" href="section-{i-1}.html">← 上一板块</a>'
            if i > 1 else '    <span></span>'
        )
        next_link = (
            f'    <a class="footer-link" href="section-{i+1}.html">下一板块 →</a>'
            if i < total else '    <span></span>'
        )

        page_body = (
            '<div class="container">\n'
            '    <div class="section-hero">\n'
            '        <div class="breadcrumb">\n'
            f'            <a href="index.html">← 首页</a>\n'
            '            <span>/</span>\n'
            f'            <span>板块 {i}</span>\n'
            '        </div>\n'
            '        <div class="section-title-wrap">\n'
            f'            <div class="section-icon">{icon}</div>\n'
            f'            <h1>{sec_title}</h1>\n'
            '        </div>\n'
            f'        <div class="section-meta">\n'
            f'            <div class="meta-item"><span class="dot"></span>{date_str}</div>\n'
            f'            <div class="meta-item"><span class="dot"></span>板块 {i} / {total}</div>\n'
            '        </div>\n'
            '    </div>\n'
            '    <div class="content-section">\n'
            + md_to_html_body(sec_md) + '\n'
            '    </div>\n'
            '    <div class="page-footer">\n'
            + prev_link + '\n'
            f'    <a class="footer-link primary" href="index.html">← 返回首页</a>\n'
            + next_link + '\n'
            '    </div>\n'
            '</div>'
        )

        (out_dir / f"section-{i}.html").write_text(
            make_page(f"{sec_title} — {page_title}", page_body), encoding="utf-8"
        )
        print(f"  ✅ section-{i}.html")

    print(f"\n🎉 生成完毕，共 {total + 1} 个 HTML 文件")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="输入的 Markdown 文件路径")
    parser.add_argument("-o", "--output", help="输出目录")
    args = parser.parse_args()
    if not generate_pages(args.input, args.output):
        sys.exit(1)

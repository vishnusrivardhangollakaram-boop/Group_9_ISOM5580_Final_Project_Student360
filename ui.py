"""Original Student360 visual system and small presentation helpers."""
from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo
import re
import streamlit as st

ROOT = Path(__file__).resolve().parent

ICONS = {
    'book': '<path d="M4 5.5c3-1 5-.5 8 1.5v14c-3-2-5-2.5-8-1.5zM20 5.5c-3-1-5-.5-8 1.5v14c3-2 5-2.5 8-1.5z"/>',
    'arrow': '<path d="M5 12h14m-6-6 6 6-6 6"/>',
    'check': '<path d="m5 12 4 4L19 6"/>',
    'shield': '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6z"/><path d="m8 11 3 3 5-5"/>',
    'file': '<path d="M14 3H5v18h14V8zM14 3v5h5M8 12h8M8 16h6"/>',
    'people': '<circle cx="9" cy="8" r="3"/><path d="M3 20v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6M21 20v-3a6 6 0 0 0-3-5"/>',
    'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'spark': '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5z"/>',
    'school': '<path d="m3 10 9-7 9 7M5 9v12h14V9M10 21v-6h4v6M9 10h6"/>',
    'search': '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>',
    'message': '<path d="M4 4h16v12H9l-5 5zM8 8h8M8 12h5"/>',
    'lock': '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3"/>',
}


def icon(name: str, size: int = 22) -> str:
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS.get(name, ICONS["file"])}</svg>'


def css(school: bool = False):
    style = (ROOT / 'assets' / 'style.css').read_text(encoding='utf-8')
    accent, tint = ('#254d87', '#edf2fa') if school else ('#087f83', '#edf9f7')
    st.html('<style>:root{--accent:' + accent + ';--accent-tint:' + tint + ';}</style><style>' + style + '</style>')


def brand(sidebar: bool = False):
    st.html(f'<div class="brand {"brand-side" if sidebar else ""}"><span class="brand-mark">{icon("book",26)}</span><div><div class="brand-name">Student<span>360</span></div><div class="brand-sub">PROGRESS, WITH PERSPECTIVE</div></div></div>')


def topbar(school: bool):
    left, right = st.columns([3, 2], vertical_alignment='center')
    with left:
        brand()
    with right:
        label = 'TEACHER / SCHOOL WORKSPACE' if school else 'PARENT PORTAL'
        st.html(f'<div class="topbar-right"><span class="workspace-pill">{icon("school" if school else "people",16)}{label}</span><span class="topbar-caption">Student progress & support</span></div>')


def hero(school: bool):
    if school:
        st.html(f'<section class="hero hero-school"><div class="hero-copy"><div class="eyebrow">THE REVIEW WORKSPACE</div><h1>Expert judgement.<br>Clearer outcomes.</h1><p>Verify the record. Refine the plan. Give families a response they can rely on.</p><div class="hero-chips"><span>{icon("shield",15)} Evidence review</span><span>{icon("check",15)} Teacher approval</span><span>{icon("file",15)} Review record</span></div></div><div class="hero-art school-art"><div class="art-ring"></div><div class="art-panel"><div class="art-panel-head">THE HUMAN PERSPECTIVE</div><div class="art-row"><span class="art-icon">{icon("search",20)}</span><div><b>Check the supporting record</b><small>Identify what is established</small></div></div><div class="art-row"><span class="art-icon">{icon("people",20)}</span><div><b>Apply professional judgement</b><small>Edit before you approve</small></div></div><div class="art-bottom">A considered response for every family {icon("arrow",17)}</div></div></div></section>')
    else:
        st.html(f'<section class="hero hero-parent"><div class="hero-copy"><div class="eyebrow">A STRONGER SCHOOL–HOME CONNECTION</div><h1>Understand progress.<br>Support what comes next.</h1><p>A clear view of your child’s learning, grounded in their records and guided by their teachers.</p><div class="hero-chips"><span>{icon("file",15)} Record-based answers</span><span>{icon("people",15)} Human review</span><span>{icon("message",15)} Your report language</span></div></div><div class="hero-art"><div class="art-ring"></div><div class="art-panel"><div class="art-panel-head">FROM QUESTION TO CLARITY</div><div class="art-row"><span class="art-icon">{icon("book",21)}</span><div><b>Learning records</b><small>The evidence behind your answer</small></div><span class="art-dot"></span></div><div class="art-row"><span class="art-icon">{icon("people",21)}</span><div><b>School & teacher review</b><small>A human decision when needed</small></div><span class="art-dot"></span></div><div class="art-bottom">One clear, considered progress report {icon("arrow",17)}</div></div></div></section>')


def section(title: str, caption: str = '', kicker: str = ''):
    kicker_html = '<div class="eyebrow">' + escape(kicker) + '</div>' if kicker else ''
    caption_html = '<p>' + escape(caption) + '</p>' if caption else ''
    st.html(f'<div class="section-heading">{kicker_html}<h2>{escape(title)}</h2>{caption_html}</div>')


def banner(title: str, description: str, tone: str = 'blue'):
    symbol = {'green': 'check', 'red': 'search', 'amber': 'clock', 'purple': 'people'}.get(tone, 'file')
    st.html(f'<div class="status-banner tone-{tone}"><div class="status-icon">{icon(symbol,24)}</div><div><b>{escape(title)}</b><p>{escape(description)}</p></div></div>')


def stat(label: str, value: object, note: str, symbol: str, tone: str = 'blue'):
    st.html(f'<div class="stat-card tone-{tone}"><div class="stat-top"><span>{escape(label)}</span><span class="stat-icon">{icon(symbol,21)}</span></div><div class="stat-value">{escape(str(value))}</div><div class="stat-note">{escape(note)}</div></div>')


def badge(text: str, tone: str = 'blue'):
    st.html(f'<span class="badge tone-{tone}"><span></span>{escape(text)}</span>')


def local_time(timestamp: float, short: bool = False) -> str:
    return datetime.fromtimestamp(timestamp, ZoneInfo('Asia/Hong_Kong')).strftime('%d %b · %H:%M' if short else '%d %b %Y, %H:%M HKT')


def case_ref(case: dict) -> str:
    return 'S360-' + case['id'][:8].upper()


def tracker(case: dict):
    phase = case['phase']
    complete = phase == 'complete'
    reviewed = bool(case.get('review_history'))
    review_label = 'Teacher review' if case.get('review_kind') == 'teacher' else 'School review'
    stages = [('Question received', True), ('Record lookup', phase in {'awaiting_review', 'complete'} or reviewed),
              (review_label if phase == 'awaiting_review' or reviewed else 'Review if needed', reviewed or complete),
              ('Response ready', complete)]
    html = '<div class="tracker">'
    for i, (label, done) in enumerate(stages):
        active = not done and (i == 1 or (i == 2 and phase == 'awaiting_review'))
        html += f'<div class="tracker-step {"done" if done else "active" if active else ""}"><span class="tracker-number">{icon("check",14) if done else i+1}</span><span>{escape(label)}</span></div>'
    st.html(html + '</div>')


def footer(school: bool):
    label = 'Teacher / School workspace' if school else 'Parent portal'
    st.html(f'<footer class="app-footer"><span>Student360 <span class="footer-separator">/</span> {label}</span><span>Thoughtful answers. Human judgement.</span></footer>')


def report_body(report: str) -> str:
    # The page already supplies the brand and report title. Keep the backend body intact.
    return re.sub(r'^# Student 360\s*\n+## [^\n]+\s*\n+', '', report, count=1)


def printable_report(case: dict) -> bytes:
    """Self-contained escaped HTML for browser printing; no scripts, API URLs or tokens."""
    def inline(value):
        value = escape(value)
        return re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', value)
    chunks, paragraph = [], []
    def flush():
        if paragraph:
            chunks.append('<p>' + '<br>'.join(paragraph) + '</p>')
            paragraph.clear()
    for line in case['report'].splitlines():
        if not line.strip():
            flush()
        elif line.startswith('#'):
            flush()
            depth = min(len(line) - len(line.lstrip('#')), 4)
            chunks.append(f'<h{depth}>' + inline(line.lstrip('#').strip()) + f'</h{depth}>')
        elif line.startswith('> '):
            flush()
            chunks.append('<aside>' + inline(line[2:]) + '</aside>')
        elif line.startswith('- '):
            flush()
            chunks.append('<p class="bullet">• ' + inline(line[2:]) + '</p>')
        else:
            paragraph.append(inline(line))
    flush()
    title = 'Student360 · ' + escape(case.get('student') or 'Progress report')
    document = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>
    body{{margin:0;background:#f2f5f8;color:#203249;font:16px/1.75 system-ui,-apple-system,sans-serif}}main{{max-width:820px;margin:40px auto;padding:50px;background:#fff;border-top:5px solid #087f83;box-shadow:0 8px 40px #1023340d}}h1{{font-size:30px;color:#12334a}}h2{{font-size:23px}}h3,h4{{font-size:18px;margin-top:28px;color:#087f83}}aside{{padding:12px 18px;background:#f0f7f6;border-left:3px solid #087f83}}.meta,footer{{color:#68778b;font-size:12px}}.bullet{{margin:3px 0}}footer{{border-top:1px solid #e4eaf0;margin-top:36px;padding-top:18px}}@media print{{body{{background:white}}main{{margin:0;padding:16px;box-shadow:none;max-width:none}}h2,h3{{break-after:avoid}}p,aside{{orphans:3;widows:3}}}}@media(max-width:700px){{main{{margin:0;padding:24px}}}}
    </style></head><body><main><div class="meta">{escape(case_ref(case))} · {escape(local_time(case['created']))}</div>{''.join(chunks)}<footer>Student360 · Prepared from the published school workflow.<br>To save as PDF, open your browser’s Print menu and select Save as PDF.</footer></main></body></html>'''
    return document.encode('utf-8')

"""Student360 presentation: purposeful imagery, native controls, real workflow states."""
from __future__ import annotations
from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo
import base64
import re
import streamlit as st

ROOT = Path(__file__).resolve().parent


@st.cache_data(show_spinner=False)
def asset_uri(filename: str) -> str:
    """Only public, bundled imagery is cached; never credentials or reports."""
    path = ROOT / 'assets' / filename
    mime = 'image/png' if path.suffix == '.png' else 'image/jpeg'
    return 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode('ascii')


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
    tokens = ('--ink:#26364d;--muted:#707d92;--accent:#334e82;--accent-deep:#172b4d;--accent-tint:#edf1fa;--canvas:#f2f4f8;--wash:#e4eaf3;--line:#dde3ed;'
              if school else '--ink:#23352f;--muted:#68756e;--accent:#286356;--accent-deep:#173f36;--accent-tint:#edf3ee;--canvas:#f7f7f2;--wash:#e8eee3;--line:#e0e6df;')
    st.html('<style>' + style + '</style><style>:root{' + tokens + '}</style>')


def brand():
    st.html(f'<div class="brand"><span class="brand-mark">{icon("book",25)}</span><div><div class="brand-name">Student<span>360</span></div><div class="brand-sub">CHRISTIAN EDUCATION</div></div></div>')


def landing_story(school: bool = False):
    photo = asset_uri('teacher_students.png' if school else 'parent_child.png')
    school_photo = asset_uri('christian_school.png')
    if school:
        kicker = 'THE SCHOOL WORKSPACE'
        title = 'Your judgement.<br><em>Their next step.</em>'
        subtitle = 'A focused space to check evidence and review learning plans.'
        alt = 'Illustrative teacher and students working through a lesson together'
        caption = 'Thoughtful support starts with you.'
    else:
        kicker = 'THE PARENT SPACE'
        title = 'Understand today.<br><em>Support tomorrow.</em>'
        subtitle = 'A clearer picture of your child’s learning, one question at a time.'
        alt = 'Illustrative parent and child learning together at home'
        caption = 'School & home. A shared next step.'
    st.html(f'<section class="landing-story {"school-story" if school else "parent-story"}"><div class="eyebrow"><span class="eyebrow-line"></span>{kicker}</div><h1>{title}</h1><p class="landing-intro">{subtitle}</p><figure class="story-photo"><img src="{photo}" alt="{alt}" fetchpriority="high"/><figcaption><span>{caption}</span>{icon("book",18)}</figcaption></figure><div class="school-signature"><img src="{school_photo}" alt="Christian Education reception"/><div><b>Christian Education</b><span>Student progress & support</span></div><span class="signature-line"></span>{icon("school",21)}</div></section>')


def school_header(reviewer: str = ''):
    name = reviewer.strip()
    welcome = 'Welcome' + (', ' + name if name else '') + '.'
    photo = asset_uri('teacher_students.png')
    school_photo = asset_uri('christian_school.png')
    st.html(f'<section class="workspace-hero"><div class="workspace-copy"><div class="eyebrow">TEACHER / SCHOOL</div><h1>{escape(welcome)}</h1><p>A clear view of the requests that need your judgement.</p><div class="workspace-school">{icon("school",16)} Christian Education</div></div><div class="workspace-photos"><img src="{photo}" alt="Illustrative teacher supporting two students"/><img class="workspace-school-photo" src="{school_photo}" alt="Christian Education school reception"/></div></section>')


def page_heading(title: str, description: str = '', kicker: str = ''):
    st.html(f'<header class="page-heading"><div class="eyebrow">{escape(kicker)}</div><h1>{escape(title)}</h1><p>{escape(description)}</p></header>')


def section(title: str, caption: str = '', kicker: str = ''):
    kicker_html = '<div class="eyebrow">' + escape(kicker) + '</div>' if kicker else ''
    caption_html = '<p>' + escape(caption) + '</p>' if caption else ''
    st.html(f'<div class="section-heading">{kicker_html}<h2>{escape(title)}</h2>{caption_html}</div>')


def banner(title: str, description: str, tone: str = 'blue'):
    symbol = {'green': 'check', 'red': 'search', 'amber': 'clock', 'purple': 'people'}.get(tone, 'file')
    st.html(f'<div class="status-banner tone-{tone}" role="status"><div class="status-icon">{icon(symbol,22)}</div><div><b>{escape(title)}</b><p>{escape(description)}</p></div></div>')


def stat(label: str, value: object, note: str, symbol: str, tone: str = 'blue'):
    st.html(f'<div class="stat-card tone-{tone}"><div class="stat-icon">{icon(symbol,23)}</div><div><div class="stat-label">{escape(label)}</div><div class="stat-value">{escape(str(value))}<span>{escape(note)}</span></div></div></div>')


def badge(text: str, tone: str = 'blue'):
    st.html(f'<span class="badge tone-{tone}"><span></span>{escape(text)}</span>')


def local_time(timestamp: float, short: bool = False) -> str:
    return datetime.fromtimestamp(timestamp, ZoneInfo('Asia/Hong_Kong')).strftime('%d %b · %H:%M' if short else '%d %b %Y, %H:%M HKT')


def case_ref(case: dict) -> str:
    return 'S360-' + case['id'][:8].upper()


def tracker(case: dict):
    """Only show a review stage when this request actually entered human review."""
    phase = case['phase']
    complete, reviewing = phase == 'complete', phase == 'awaiting_review'
    reviewed = bool(case.get('review_history')) or case.get('metadata', {}).get('review_status') in {'teacher_approved', 'staff_confirmed', 'not_approved', 'timed_out'}
    stages = [('Request received', 'done'), ('Preparing response', 'done' if reviewing or complete else 'active')]
    if reviewing or reviewed:
        label = 'Teacher review' if case.get('review_kind') == 'teacher' else 'School review'
        stages.append((label, 'active' if reviewing else 'done'))
    stages.append(('Response ready', 'done' if complete else 'waiting'))
    parts = []
    for i, (label, state) in enumerate(stages):
        number = icon('check', 13) if state == 'done' else str(i+1)
        parts.append(f'<div class="tracker-step {state}"><span class="tracker-number">{number}</span><span>{escape(label)}</span></div>')
    st.html('<div class="tracker" aria-label="Request progress">' + ''.join(parts) + '</div>')


def install_motion(enabled: bool = True):
    script = (ROOT / 'assets' / 'scroll.js').read_text(encoding='utf-8')
    flag = 'true' if enabled else 'false'
    # Only trusted local code is executable. Reports and questions never enter it.
    st.html('<div data-s360-controller data-s360-autoscroll="' + flag + '" style="display:none"></div><script>' + script + '</script>', unsafe_allow_javascript=True)


def anchor(name: str):
    if name in {'s360-top', 's360-question', 's360-request', 's360-report', 's360-review', 's360-progress'}:
        st.html(f'<div id="{name}" class="scroll-anchor" aria-hidden="true"></div>')


def scroll_anchor(name: str, event_key: str):
    if name in {'s360-top', 's360-request', 's360-report', 's360-review', 's360-progress'}:
        st.html(f'<div id="{name}" class="scroll-anchor" data-s360-scroll-key="{escape(event_key, quote=True)}" aria-hidden="true"></div>')


def back_to_top():
    st.html('<button type="button" class="back-to-top" data-s360-scroll-to="s360-top" aria-label="Back to top">↑ <span>Top</span></button>')


def footer(school: bool):
    label = 'Teacher / School workspace' if school else 'Parent portal'
    st.html(f'<footer class="app-footer"><span><b>Student360</b><span class="footer-separator">/</span>Christian Education</span><span>{label}</span></footer>')


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
    body{{margin:0;background:#f7f7f2;color:#203249;font:16px/1.75 system-ui,-apple-system,sans-serif}}main{{max-width:820px;margin:40px auto;padding:50px;background:#fff;border-top:5px solid #286356;box-shadow:0 8px 40px #1023340d}}h1{{font-size:30px;color:#12334a}}h2{{font-size:23px}}h3,h4{{font-size:18px;margin-top:28px;color:#286356}}aside{{padding:12px 18px;background:#f0f7f6;border-left:3px solid #286356}}.meta,footer{{color:#68778b;font-size:12px}}.bullet{{margin:3px 0}}footer{{border-top:1px solid #e4eaf0;margin-top:36px;padding-top:18px}}@media print{{body{{background:white}}main{{margin:0;padding:16px;box-shadow:none;max-width:none}}h2,h3{{break-after:avoid}}p,aside{{orphans:3;widows:3}}}}@media(max-width:700px){{main{{margin:0;padding:24px}}}}
    </style></head><body><main><div class="meta">{escape(case_ref(case))} · {escape(local_time(case['created']))}</div>{''.join(chunks)}<footer>Student360 · Prepared from the published school workflow.<br>To save as PDF, open your browser’s Print menu and select Save as PDF.</footer></main></body></html>'''
    return document.encode('utf-8')

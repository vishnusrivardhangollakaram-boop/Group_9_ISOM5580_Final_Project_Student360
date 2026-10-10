"""Student360 presentation: purposeful imagery, native controls, real workflow states."""
from __future__ import annotations
from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo
import base64
import re
import streamlit as st
from i18n import t, language, LANGUAGE_CODES

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
    # An image keeps the vector isolated from st.html's inline-SVG sanitization.
    # The source is a fixed local icon set, never user-provided markup.
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="#334c63" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{ICONS.get(name, ICONS["file"])}</svg>'
    source = base64.b64encode(svg.encode('utf-8')).decode('ascii')
    return f'<img class="ui-icon" src="data:image/svg+xml;base64,{source}" width="{size}" height="{size}" alt="" aria-hidden="true"/>'


def css(school: bool = False):
    style = (ROOT / 'assets' / 'style.css').read_text(encoding='utf-8')
    tokens = ('--ink:#17283f;--muted:#6a7688;--accent:#345bb2;--accent-deep:#172d50;--accent-tint:#eef2fc;--canvas:#f5f6fa;--line:#e2e6ef;'
              if school else '--ink:#172d39;--muted:#697780;--accent:#147d74;--accent-deep:#123c42;--accent-tint:#edf7f5;--canvas:#f8fafb;--line:#e2e9ec;')
    st.html('<style>' + style + '</style><style>:root{' + tokens + '}</style>')


def brand():
    st.html('<div class="brand" aria-label="Student360, Christian Education"><div class="brand-name">student<span>360</span><i></i></div><div class="brand-sub">' + escape(t('CHRISTIAN EDUCATION')) + '</div></div>')


def landing_story(school: bool = False):
    photo = asset_uri('school_portrait.png' if school else 'parent_portrait.png')
    if school:
        kicker = 'TEACHER & SCHOOL'
        title = escape(t('Your expertise.')) + '<br>' + escape(t('Their way forward.'))
        subtitle = 'Thoughtful decisions. Meaningful support.'
        alt = 'Illustrative teacher and students working through a lesson together'
    else:
        kicker = 'FOR PARENTS'
        title = escape(t('A clearer picture.')) + '<br>' + escape(t('A better next step.'))
        subtitle = 'Stay close to your child’s learning.'
        alt = 'Illustrative parent and child learning together at home'
    st.html(f'<section class="landing-story {"school-story" if school else "parent-story"}"><img class="hero-photo" src="{photo}" alt="{escape(t(alt))}" fetchpriority="high"/><div class="hero-shade"></div><div class="hero-label">{escape(t(kicker))}</div><div class="hero-copy"><div class="hero-rule"></div><h1>{title}</h1><p>{escape(t(subtitle))}</p></div></section>')



def school_showcase():
    photo = asset_uri('christian_school.png')
    st.html(f'<section class="school-showcase"><div class="school-showcase-copy"><div class="eyebrow">{escape(t("OUR SCHOOL"))}</div><h2>{escape(t("Christian Education"))}</h2><p>{escape(t("Your school. Your learning community."))}</p><span>{escape(t("A shared place for progress, questions and the next step."))}</span></div><img src="{photo}" alt="{escape(t("Christian Education school reception"))}" loading="lazy"/></section>')
    with st.expander(t('View the full school photograph')):
        st.image(str(ROOT / 'assets' / 'christian_school.png'), caption=t('Christian Education school reception'), width='stretch')


def school_header(reviewer: str = ''):
    name = reviewer.strip()
    if name == 'School reviewer':
        name = t(name)
    welcome = t('Welcome, {name}.', name=name) if name else t('Welcome.')
    photo = asset_uri('christian_school.png')
    st.html(f'<section class="workspace-hero"><div class="workspace-copy"><div class="eyebrow">{escape(t("THE SCHOOL WORKSPACE"))}</div><h1>{escape(welcome)}</h1><p>{escape(t("Every thoughtful review makes a difference."))}</p><div class="workspace-school">{escape(t("CHRISTIAN EDUCATION"))}</div></div><div class="workspace-school-image"><img src="{photo}" alt="{escape(t("Christian Education school reception"))}"/></div></section>')


def page_heading(title: str, description: str = '', kicker: str = ''):
    st.html(f'<header class="page-heading"><div class="eyebrow">{escape(t(kicker))}</div><h1>{escape(t(title))}</h1><p>{escape(t(description))}</p></header>')


def section(title: str, caption: str = '', kicker: str = ''):
    kicker_html = '<div class="eyebrow">' + escape(t(kicker)) + '</div>' if kicker else ''
    caption_html = '<p>' + escape(t(caption)) + '</p>' if caption else ''
    st.html(f'<div class="section-heading">{kicker_html}<h2>{escape(t(title))}</h2>{caption_html}</div>')


def banner(title: str, description: str, tone: str = 'blue'):
    symbol = {'green': 'check', 'red': 'search', 'amber': 'clock', 'purple': 'people'}.get(tone, 'file')
    st.html(f'<div class="status-banner tone-{tone}" role="status"><div class="status-icon">{icon(symbol,22)}</div><div><b>{escape(t(title))}</b><p>{escape(t(description))}</p></div></div>')


def stat(label: str, value: object, note: str, symbol: str, tone: str = 'blue'):
    st.html(f'<div class="stat-card tone-{tone}"><div class="stat-icon">{icon(symbol,23)}</div><div><div class="stat-label">{escape(t(label))}</div><div class="stat-value">{escape(str(value))}<span>{escape(t(note))}</span></div></div></div>')


def badge(text: str, tone: str = 'blue'):
    st.html(f'<span class="badge tone-{tone}"><span></span>{escape(t(text))}</span>')


def local_time(timestamp: float, short: bool = False) -> str:
    value = datetime.fromtimestamp(timestamp, ZoneInfo('Asia/Hong_Kong'))
    if language() != 'English':
        return value.strftime('%m月%d日 · %H:%M' if short else '%Y年%m月%d日 %H:%M HKT')
    return value.strftime('%d %b · %H:%M' if short else '%d %b %Y, %H:%M HKT')


def case_ref(case: dict) -> str:
    return 'S360-' + case['id'][:8].upper()


def tracker(case: dict):
    """Only show a review stage when this request actually entered human review."""
    phase = case['phase']
    if phase == 'interrupted' and not case.get('run_id'):
        return
    complete, reviewing = phase == 'complete', phase == 'awaiting_review'
    reviewed = bool(case.get('review_history')) or case.get('metadata', {}).get('review_status') in {'teacher_approved', 'staff_confirmed', 'not_approved', 'timed_out'}
    stages = [('Request received', 'done'), ('Preparing response', 'done' if reviewing or complete else 'active')]
    if reviewing or reviewed:
        label = 'Teacher review' if case.get('review_kind') == 'teacher' else 'School review'
        stages.append((label, 'active' if reviewing else 'done'))
    stages.append(('Response ready', 'done' if complete else 'waiting'))
    parts = []
    for i, (label, state) in enumerate(stages):
        number = '&#10003;' if state == 'done' else str(i+1)
        parts.append(f'<div class="tracker-step {state}"><span class="tracker-number">{number}</span><span>{escape(t(label))}</span></div>')
    st.html('<div class="tracker" aria-label="' + escape(t('Request progress')) + '">' + ''.join(parts) + '</div>')


def install_motion(enabled: bool = True):
    script = (ROOT / 'assets' / 'scroll.js').read_text(encoding='utf-8')
    flag = 'true' if enabled else 'false'
    # Only trusted local code is executable. Reports and questions never enter it.
    locale = LANGUAGE_CODES[language()]
    st.html('<div data-s360-controller data-s360-language="' + locale + '" data-s360-autoscroll="' + flag + '" style="display:none"></div><script>' + script + '</script>', unsafe_allow_javascript=True)


def anchor(name: str):
    if name in {'s360-top', 's360-question', 's360-request', 's360-report', 's360-review', 's360-progress'}:
        st.html(f'<div id="{name}" class="scroll-anchor" aria-hidden="true"></div>')


def scroll_anchor(name: str, event_key: str):
    if name in {'s360-top', 's360-request', 's360-report', 's360-review', 's360-progress'}:
        st.html(f'<div id="{name}" class="scroll-anchor" data-s360-scroll-key="{escape(event_key, quote=True)}" aria-hidden="true"></div>')


def back_to_top():
    st.html('<button type="button" class="back-to-top" data-s360-scroll-to="s360-top" aria-label="' + escape(t('Back to top')) + '">↑ <span>' + escape(t('Top')) + '</span></button>')


def footer(school: bool):
    label = 'Teacher / School workspace' if school else 'Parent portal'
    st.html(f'<footer class="app-footer"><span><b>Student360</b><span class="footer-separator">/</span>{escape(t("Christian Education"))}</span><span>{escape(t(label))}</span></footer>')


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
    report_language = case.get('report_language', 'English')
    title = 'Student360 · ' + escape(case.get('student') or t('Progress report', locale=report_language))
    report_locale = LANGUAGE_CODES.get(report_language, 'en')
    source_note = escape(t('Prepared from the published school workflow.', locale=report_language))
    print_note = escape(t('To save as PDF, open your browser’s Print menu and select Save as PDF.', locale=report_language))
    document = f'''<!doctype html><html lang="{report_locale}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>
    body{{margin:0;background:#f7f7f2;color:#203249;font:16px/1.75 system-ui,-apple-system,sans-serif}}main{{max-width:820px;margin:40px auto;padding:50px;background:#fff;border-top:5px solid #286356;box-shadow:0 8px 40px #1023340d}}h1{{font-size:30px;color:#12334a}}h2{{font-size:23px}}h3,h4{{font-size:18px;margin-top:28px;color:#286356}}aside{{padding:12px 18px;background:#f0f7f6;border-left:3px solid #286356}}.meta,footer{{color:#68778b;font-size:12px}}.bullet{{margin:3px 0}}footer{{border-top:1px solid #e4eaf0;margin-top:36px;padding-top:18px}}@media print{{body{{background:white}}main{{margin:0;padding:16px;box-shadow:none;max-width:none}}h2,h3{{break-after:avoid}}p,aside{{orphans:3;widows:3}}}}@media(max-width:700px){{main{{margin:0;padding:24px}}}}
    </style></head><body><main><div class="meta">{escape(case_ref(case))} · {escape(local_time(case['created']))}</div>{''.join(chunks)}<footer>Student360 · {source_note}<br>{print_note}</footer></main></body></html>'''
    return document.encode('utf-8')

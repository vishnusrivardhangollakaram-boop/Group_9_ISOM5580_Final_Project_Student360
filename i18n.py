"""Local interface translations. Dify alone generates/translates final reports.

Stable English values stay in routes, action IDs and API payloads. Only display
text passes through t(). Questions, evidence and approved plans stay verbatim.
"""
from __future__ import annotations
import json
from pathlib import Path
import re
import streamlit as st

LANGUAGES = ['English', 'Chinese (Simplified) 简体中文', 'Chinese (Traditional) 繁體中文']
LANGUAGE_LABELS = dict(zip(LANGUAGES, ['English', '简体中文', '繁體中文']))
LANGUAGE_CODES = dict(zip(LANGUAGES, ['en', 'zh-CN', 'zh-TW']))


def language() -> str:
    selected = st.session_state.get('ui_language', 'English')
    return selected if selected in LANGUAGES else 'English'


@st.cache_data(show_spinner=False)
def catalog(code: str) -> dict[str, str]:
    if code == 'en':
        return {}
    return json.loads((Path(__file__).parent / 'locales' / (code + '.json')).read_text(encoding='utf-8'))


def t(message: str, *, locale: str | None = None, **values) -> str:
    message = str(message)
    code = LANGUAGE_CODES.get(locale or language(), 'en')
    translated = catalog(code).get(message, message)
    return translated.format(**values) if values else translated


def localize_diagnostic(message: str) -> str:
    """Translate our messages, preserving the server's original technical detail."""
    output = []
    for line in str(message).splitlines():
        if line.startswith('Dify response: '):
            output.append(t('Dify response:') + ' ' + line[len('Dify response: '):])
        else:
            output.append(t(line))
    return '\n'.join(output)


def localize_review_content(content: str) -> str:
    """Translate known template labels/instructions without rewriting source data.

    Match exact standalone lines or known bold label prefixes. Never translate
    a student's name, a retrieved quotation, a draft or a reviewer's submitted text.
    """
    lines = []
    in_source_records = False
    for line in content.splitlines():
        heading = re.match(r'^(#{1,6} )(.+)$', line)
        prefix = re.match(r'^\*\*([^*]+):\*\*(.*)$', line)
        if heading and heading[2] == 'Record extract or verified school correction':
            in_source_records = False
        if in_source_records:
            lines.append(line)
            continue
        if heading:
            lines.append(heading[1] + t(heading[2]))
            if heading[2] == 'Relevant record extracts':
                in_source_records = True
        elif prefix:
            tail = prefix[2]
            if prefix[1] in {'Confirm existing record', 'Use supplied school record', 'Request missing records'}:
                tail = ' ' + t(tail.strip())
            lines.append('**' + t(prefix[1]) + ':**' + tail)
        else:
            lines.append(t(line))
    return '\n'.join(lines)

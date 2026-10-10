"""Student360 — Parent portal and Teacher/School review workspace.

Run: streamlit run app.py
Connection credentials belong only in .streamlit/secrets.toml / Cloud Secrets.
"""
from __future__ import annotations

from html import escape
import hashlib
import hmac
import json
import re
import time

import streamlit as st

from config import load_settings
from dify_client import DifyClient, DifyError
from store import CaseStore
from workflow import display_state, execute, refresh_result, rendered_form_content, submit_review
import ui
from i18n import t, language, LANGUAGES, LANGUAGE_LABELS, LANGUAGE_CODES, localize_diagnostic, localize_review_content

if "ui_language" not in st.session_state:
    st.session_state.ui_language = next((name for name, code in LANGUAGE_CODES.items() if code == st.query_params.get("lang")), "English")

st.set_page_config(page_title=t('Student360 | Progress & support'), page_icon=str(ui.ROOT / 'assets' / 'favicon.svg'),
                   layout='wide', initial_sidebar_state='collapsed',
                   menu_items={'Get Help': None, 'Report a bug': None, 'About': t('Student360 · Record-based progress answers and human-reviewed learning plans.')})

EXAMPLES = [
    ('Taylor', 'Recorded progress', 'What is Taylor’s latest recorded official IELTS result, including the date and all section scores?'),
    ('Riley', 'Check a specific result', 'What was Riley’s official PET listening score on February 28, 2026?'),
    ('Skyler', 'Request a support plan', 'Create a one-week listening support plan for Skyler based on the report and teacher feedback.'),
    ('Vishnu', 'Find a student record', 'Show the learning progress report for Vishnu.'),
]

try:
    settings = load_settings()
except (ValueError, OSError) as exc:
    st.error(t('The separate configuration file could not be read. Check its TOML format and restart the app.'))
    st.stop()


@st.cache_resource
def case_store(path: str) -> CaseStore:
    from pathlib import Path
    return CaseStore(Path(path))


store = case_store(str(settings.database_path))
client = None
connection_error = ''
try:
    client = DifyClient(settings.api_base_url, settings.api_key)
except DifyError as exc:
    connection_error = str(exc)

defaults = {
    'portal': 'Teacher / School' if st.query_params.get('view') == 'school' else 'Parent',
    'question': '', 'student_name': '', 'parent_cases': [],
    'parent_active': '', 'school_active': '', 'school_auth': '', 'reviewer_name': '',
    'parent_page': 'Ask a question', 'school_page': 'Review inbox',
    'auto_scroll': True, 'focus_epoch': 0,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

public_token = st.query_params.get('request', '')
if public_token:
    restored = store.get_public(public_token)
    if restored:
        st.session_state.parent_active = restored['id']
        if restored['id'] not in st.session_state.parent_cases:
            st.session_state.parent_cases.append(restored['id'])


ACTION_LABELS = {
    'approve_plan': 'Approve reviewed plan', 'reject_plan': 'Decline / revise plan',
    'confirm_existing': 'Confirm existing record', 'use_school_record': 'Use supplied school record',
    'request_records': 'Request missing records',
}
FIELD_LABELS = {'final_plan': 'Reviewed plan', 'record_extract': 'Record extract or verified school correction',
                'record_reference': 'Record reference · optional', 'review_note': 'School note · optional'}


def change_language():
    st.query_params['lang'] = LANGUAGE_CODES[language()]


def select_portal(portal: str):
    st.session_state.portal = portal
    st.query_params['view'] = 'school' if portal == 'Teacher / School' else 'parent'
    st.session_state.focus_epoch += 1


def navigate(page: str, school: bool = False):
    if school:
        st.session_state.school_page = page
        st.session_state.school_active = ''
    else:
        st.session_state.parent_page = page
        if page == 'Ask a question':
            st.session_state.parent_active = ''
            st.query_params.pop('request', None)
    st.session_state.focus_epoch += 1


def sign_out():
    st.session_state.school_auth = ''
    st.session_state.school_active = ''
    st.session_state.reviewer_name = ''
    st.session_state.pop('reviewer_editor', None)


def choose_example(name: str, question: str):
    st.session_state.student_name = name
    st.session_state.question = t(question)
    st.session_state.parent_page = 'Ask a question'


def activate_parent(case: dict):
    st.session_state.parent_active = case['id']
    st.query_params['request'] = case['public_token']


def open_parent_report(case: dict):
    activate_parent(case)
    st.session_state.parent_page = 'Ask a question'
    st.session_state.focus_epoch += 1


def reuse_question(case: dict):
    """Return a retained question to the form without starting a duplicate run."""
    st.session_state.question = case['question']
    st.session_state.student_name = case.get('student') or ''
    navigate('Ask a question')


def auth_digest() -> str:
    return hashlib.sha256(settings.school_access_code.encode('utf-8')).hexdigest()


def school_authenticated() -> bool:
    return not settings.school_access_code or hmac.compare_digest(st.session_state.school_auth, auth_digest())


def render_empty(title: str, description: str, symbol: str = 'file'):
    st.html(f'<div class="empty-state"><div class="empty-icon">{ui.icon(symbol,25)}</div><h3>{escape(t(title))}</h3><p>{escape(t(description))}</p></div>')


def friendly_step(title: str) -> str:
    text = title.lower()
    if 'translat' in text or 'language' in text:
        return 'Preparing your report in the chosen language…'
    if 'student' in text and ('find' in text or 'name' in text):
        return 'Finding the student’s learning record…'
    if 'teacher' in text:
        return 'Checking whether teacher review is needed…'
    if 'school' in text or 'verified record' in text:
        return 'Checking the school-verified information…'
    if 'answer' in text or 'report' in text or 'response' in text:
        return 'Preparing a clear progress response…'
    return 'Checking the supporting learning records…'


def run_request(case_id: str, start: bool = False):
    if not client:
        return
    ui.scroll_anchor('s360-progress', 'progress-' + case_id + '-' + str(st.session_state.focus_epoch))
    with st.status(t('Preparing the request…'), expanded=False) as progress:
        execute(client, store, case_id, start=start,
                progress=lambda title: progress.update(label=t(friendly_step(title))))
        case = store.get(case_id)
        label, _, _ = display_state(case)
        progress.update(label=t(label), state='error' if case['phase'] == 'interrupted' else 'complete')


def render_report(case: dict, school: bool = False):
    ui.scroll_anchor('s360-report', ('school-report-' if school else 'parent-report-') + case['id'] + '-' + str(st.session_state.focus_epoch))
    with st.container(key='report_card'):
        head, download = st.columns([4, 1.5], vertical_alignment='center')
        file_stub = 'Student360_' + re.sub(r'[^A-Za-z0-9_-]', '_', case.get('student') or 'Report') + '_' + case['id'][:8]
        with head:
            ui.section('Student progress report', ui.case_ref(case) + ' · ' + ui.local_time(case['created']))
        with download:
            with st.popover(t('Download report'), width='stretch'):
                st.download_button(t('Printable report'), ui.printable_report(case), file_name=file_stub + '.html',
                                   mime='text/html', width='stretch', key='print_' + case['id'])
                st.download_button(t('Markdown file'), case['report'].encode('utf-8'), file_name=file_stub + '.md',
                                   mime='text/markdown', width='stretch', key='md_' + case['id'])
                st.caption(t('Open the printable file → Print → Save as PDF.'))
        st.markdown(ui.report_body(case['report']))
    if school and case.get('review_history'):
        with st.expander(t('School review record')):
            for i, entry in enumerate(case['review_history']):
                reviewer = t('School reviewer') if entry['reviewer'] == 'School reviewer' else entry['reviewer']
                st.markdown('**' + reviewer + '** · ' + ui.local_time(entry['at']))
                st.caption(t('Decision: {action}', action=t(ACTION_LABELS.get(entry['action'], entry['action']))))
                for key, value in entry.get('inputs', {}).items():
                    if value:
                        st.markdown('**' + t(FIELD_LABELS.get(key, key)) + '**')
                        st.text(value)
            record = {k: case[k] for k in ['question', 'report_language', 'student', 'created', 'report', 'review_history']}
            st.download_button(t('Download review record'), json.dumps(record, ensure_ascii=False, indent=2),
                               file_name=file_stub + '_review.json', mime='application/json', key='audit_' + case['id'])


@st.fragment(run_every='8s')
def parent_live_report(case_id: str):
    case = store.get(case_id)
    if not case:
        render_empty('This request is no longer available', 'The server’s temporary request inbox may have been reset. Please send a new question.')
        return
    if client and case['phase'] != 'complete':
        refresh_result(client, store, case_id)
        case = store.get(case_id)
    label, note, tone = display_state(case)
    if case['phase'] != 'complete':
        ui.scroll_anchor('s360-request', 'parent-request-' + case_id + '-' + case['phase'] + '-' + case.get('review_kind', '') + '-' + str(st.session_state.focus_epoch))
    else:
        ui.anchor('s360-request')
    ui.page_heading(case.get('student') or 'Your request', ui.case_ref(case) + ' · ' + ui.local_time(case['created']), 'YOUR LEARNING CONVERSATION')
    if case['phase'] in {'complete', 'interrupted'}:
        ui.banner(label, note, tone)
    if case['phase'] != 'complete':
        ui.tracker(case)
    with st.expander(t('View your question')):
        st.write(case['question'])
        st.caption(t(ui.case_ref(case) + ' · ' + ui.local_time(case['created']) + ' · ' + LANGUAGE_LABELS[case['report_language']]))
    if case['phase'] == 'complete':
        render_report(case)
    elif case['phase'] == 'awaiting_review':
        teacher = case['review_kind'] == 'teacher'
        title = 'Waiting for teacher review' if teacher else 'More evidence is needed'
        description = ('The response will update here after the teacher’s decision.'
                       if teacher else 'More supporting information is needed. Your report will update after the school’s review.')
        render_empty(title, description, 'people' if teacher else 'search')
        st.caption(t('This page updates automatically. Bookmark it to return to this request.'))
    elif case['phase'] == 'interrupted':
        if case['run_id'] and client:
            if st.button(t('Reconnect to this request'), type='primary', key='parent_reconnect_' + case_id):
                run_request(case_id)
                st.rerun()
        else:
            with st.container(key='connection_card'):
                ui.section('Your question is saved.', 'Once the connection is restored, you can submit it again.')
                if st.button(t('Use this question again'), type='primary', key='reuse_' + case_id):
                    reuse_question(case)
                    st.rerun()
        with st.expander(t('Connection details')):
            st.text(localize_diagnostic(case.get('error') or 'The report connection needs attention.'))
            if case.get('error_status') in {401, 403} or 'connection was denied' in case.get('error', ''):
                st.caption(t('App owner: enable the Service API in the published Dify app, confirm its app key in Streamlit Secrets, then reboot Streamlit. See README → HTTP 403.'))
            elif not case.get('run_id'):
                st.caption(t('No workflow ID was received. Check Dify Logs before resubmitting if the connection timed out; a run may already exist.'))
    else:
        render_empty('Your report is being prepared', 'The school workflow is checking the available information. You can keep this page open.', 'clock')
        if case['run_id'] and client and not store.busy(case_id):
            if st.button(t('Continue preparing the report'), key='continue_' + case_id):
                run_request(case_id)
                st.rerun()


def question_form():
    with st.container(key='question_card'):
        ui.section('Start with a question.', 'Progress, results or a little extra support.', 'YOUR CHILD’S LEARNING')
        # Native controls sync their values before a global language switch.
        student = st.text_input(t('Student name'), key='student_name', placeholder=t('e.g. Taylor'), max_chars=60,
                                help=t('You can also include the name directly in your question.'))
        selected_language = language()
        st.caption(t('Report language: {language}', language=LANGUAGE_LABELS[selected_language]))
        question = st.text_area(t('Your question'), key='question', height=150, max_chars=1900,
                                placeholder=t('What is my child doing well? Where could they use a little more support?'))
        submitted = st.button(t('Get a progress report  →'), type='primary', width='stretch', disabled=not client, key='send_question')
        if submitted:
            q = question.strip()
            if not q:
                st.warning(t('Please enter your question.'))
            else:
                student = student.strip()
                if student and not re.search(r'\b' + re.escape(student) + r'\b', q, re.I):
                    q = t('Question about {student}: {question}', student=student, question=q)
                names = [n for n in ['Taylor', 'Riley', 'Skyler', 'Vishnu'] if re.search(r'\b' + n + r'\b', q, re.I)]
                alias = names[0] if len(names) == 1 else student
                case = store.create(q, selected_language, alias)
                st.session_state.parent_cases.append(case['id'])
                activate_parent(case)
                st.session_state.focus_epoch += 1
                run_request(case['id'], start=True)
                st.rerun()
        st.html('<div class="form-note">' + ui.icon('people',17) + '<span>' + escape(t('School or teacher review is requested when needed.')) + '</span></div>')
        with st.expander(t('Explore with an example')):
            st.html('<div class="demo-intro">' + escape(t('Choose a question, then create its report.')) + '</div>')
            with st.container(key='demo_questions'):
                for offset in (0, 2):
                    columns = st.columns(2, gap='small')
                    for col, (name, topic, prompt) in zip(columns, EXAMPLES[offset:offset+2]):
                        with col:
                            st.button(t(name + ' · ' + t(topic)), key='example_' + name, width='stretch',
                                      on_click=choose_example, args=(name, prompt))


def parent_question_view():
    ui.anchor('s360-question')
    if st.session_state.parent_active:
        parent_live_report(st.session_state.parent_active)
        return
    with st.container(key='parent_landing'):
        story, form = st.columns([1, 1.08], gap='large')
        with story:
            ui.landing_story()
        with form:
            question_form()
    ui.school_showcase()


def parent_history_view():
    ui.page_heading('Your learning conversations.', 'Requests from this browser session, together in one place.', 'MY REPORTS')
    cases = [store.get(i) for i in reversed(st.session_state.parent_cases)]
    cases = [c for c in cases if c]
    if not cases:
        render_empty('Your progress reports will appear here', 'Start with a question in the Parent portal. You can return to each request using its bookmarked URL.', 'book')
        return
    for case in cases:
        label, _, tone = display_state(case)
        with st.container(key='case_card_parent_' + case['id']):
            copy, state, action = st.columns([3.7, 1.8, 1], vertical_alignment='center')
            with copy:
                case_summary(case)
            with state:
                ui.badge(label, tone)
            with action:
                st.button(t('Open →'), key='open_parent_' + case['id'], width='stretch',
                          on_click=open_parent_report, args=(case,))


def school_login():
    story, login = st.columns([1, 1.08], gap='large')
    with story:
        ui.landing_story(school=True)
    with login, st.container(key='login_card'):
        ui.section('Good to have you here.', 'Sign in to review evidence and learning plans.', 'STAFF WORKSPACE')
        with st.form('school_login'):
            reviewer = st.text_input(t('Your name'), placeholder=t('e.g. Ms. Chen'), max_chars=80, key='login_name',
                                    help=t('Included with your decisions in the school review record.'))
            code = st.text_input(t('School access code'), type='password', placeholder=t('Enter your school access code'), key='login_code')
            submitted = st.form_submit_button(t('Open school workspace  →'), type='primary', width='stretch')
        if submitted:
            if hmac.compare_digest(code.encode('utf-8'), settings.school_access_code.encode('utf-8')):
                st.session_state.school_auth = auth_digest()
                st.session_state.reviewer_name = reviewer.strip() or 'School reviewer'
                st.session_state.pop('reviewer_editor', None)
                st.session_state.focus_epoch += 1
                st.rerun()
            else:
                st.error(t('The school access code did not match.'))
        st.html('<div class="form-note">' + ui.icon('lock',16) + '<span>' + escape(t('For teachers and school reviewers.')) + '</span></div>')
    ui.school_showcase()


def case_summary(case: dict, kind: str = ''):
    name = case.get('student') or t('Student progress')
    monogram = ''.join(word[0] for word in name.split()[:2]).upper()
    kind_html = '<small>' + escape(t(kind)) + '</small>' if kind else ''
    st.html(f'<div class="case-copy"><span class="student-monogram">{escape(monogram)}</span><div class="case-content"><div class="mini-label">{escape(ui.case_ref(case))} · {escape(ui.local_time(case["created"], True))}</div><div class="case-title">{escape(name)}{kind_html}</div><div class="case-question">{escape(case["question"])}</div></div></div>')


def school_case_card(case: dict):
    label, _, tone = display_state(case)
    with st.container(key='case_card_school_' + case['id']):
        copy, state, action = st.columns([3.7, 1.8, 1.1], vertical_alignment='center')
        with copy:
            has_review = case['phase'] == 'awaiting_review' or bool(case.get('review_history'))
            kind = ('Learning plan' if case.get('review_kind') == 'teacher' else 'School evidence') if has_review else 'Progress response'
            case_summary(case, kind)
        with state:
            ui.badge(label, tone)
        with action:
            button = 'Review →' if case['phase'] == 'awaiting_review' else 'Open →'
            if st.button(t(button), key='open_school_' + case['id'], width='stretch', type='primary' if case['phase'] == 'awaiting_review' else 'secondary'):
                st.session_state.school_active = case['id']
                st.session_state.focus_epoch += 1
                st.rerun()


@st.fragment(run_every='10s')
def school_inbox(completed: bool = False):
    if not school_authenticated():
        return
    cases = store.list()
    # These counts describe the app inbox; no fictional scores or fabricated trend data.
    record_cases = [c for c in cases if c['phase'] == 'awaiting_review' and c.get('review_kind') != 'teacher']
    teacher_cases = [c for c in cases if c['phase'] == 'awaiting_review' and c.get('review_kind') == 'teacher']
    finished = [c for c in cases if c['phase'] == 'complete']
    a, b, c = st.columns(3)
    with a:
        ui.stat('School evidence', len(record_cases), 'awaiting review', 'search', 'amber')
    with b:
        ui.stat('Learning plans', len(teacher_cases), 'awaiting a decision', 'people', 'purple')
    with c:
        ui.stat('Completed', len(finished), 'responses ready', 'file', 'green')
    ui.section('Completed reports' if completed else 'Review inbox',
               'Completed responses and their review records.' if completed else 'The next step starts with your review.')
    search, filter_col = st.columns([3, 1.5])
    with search:
        query = st.text_input(t('Find a request'), placeholder=t('Search student, question or request reference'), key='school_search_' + str(completed))
    with filter_col:
        if completed:
            category = 'All completed'
        else:
            category = st.selectbox(t('Request type'), ['All active', 'Record verification', 'Teacher review', 'Needs attention'], key='school_filter_active', format_func=t)
    selected = finished if completed else [c for c in cases if c['phase'] != 'complete']
    if category == 'Record verification':
        selected = [c for c in selected if c['phase'] == 'awaiting_review' and c.get('review_kind') != 'teacher']
    elif category == 'Teacher review':
        selected = [c for c in selected if c['phase'] == 'awaiting_review' and c.get('review_kind') == 'teacher']
    elif category == 'Needs attention':
        selected = [c for c in selected if c['phase'] == 'interrupted']
    if query.strip():
        q = query.strip().casefold()
        selected = [c for c in selected if q in (c['student'] + ' ' + c['question'] + ' ' + ui.case_ref(c)).casefold()]
    if not selected:
        filtered = bool(query.strip()) or category not in {'All active', 'All completed'}
        if filtered:
            render_empty('No matching requests', 'Try another name, request reference or filter.', 'search')
        else:
            render_empty('No completed reports yet' if completed else 'You’re all caught up.',
                         'Completed responses will appear here.' if completed else 'Requests appear here when the workflow needs school evidence or a teacher’s decision.', 'check')
    else:
        st.caption(t('{shown} of {total} matching requests · Updates automatically', shown=min(len(selected), 50), total=len(selected)))
        for case in selected[:50]:
            school_case_card(case)
        if len(selected) > 50:
            st.caption(t('Showing the latest 50 matches. Use the search to narrow the inbox.'))


def review_fields(case: dict):
    form = case['form']
    teacher = case['review_kind'] == 'teacher'
    expiry = form.get('expiration_time')
    expired = bool(expiry and float(expiry) <= time.time())
    left, right = st.columns([1, 1.1], gap='large')
    with left:
        with st.container(key='school_context'):
            ui.section('Review context', 'Question & supporting records.')
            content = rendered_form_content(form)
            content = re.sub(r'^## [^\n]+\n*', '', content, count=1)
            # Keep the actual backend context available, with detailed instructions
            # behind an expander rather than duplicating them next to the editor.
            cutoff = re.search(r'\n### (?:Plan to review and edit|Record extract or verified school correction)', content)
            concise_context = content[:cutoff.start()] if cutoff else content
            records = re.search(r'\n### Relevant record extracts', concise_context)
            if records:
                st.markdown(localize_review_content(concise_context[:records.start()].strip()))
                with st.expander(t('Supporting record extracts')):
                    st.markdown(localize_review_content(concise_context[records.start():].strip()))
            else:
                st.markdown(localize_review_content(concise_context.strip()))
            with st.expander(t('Full review instructions')):
                st.markdown(localize_review_content(content))
            st.caption(t('Original school records and reviewed text are kept in their source language.'))
    with right:
        with st.container(key='school_review'):
            ui.section('Review the learning plan' if teacher else 'Verify the school record',
                       'Edit the proposed plan before making your decision.' if teacher else 'Provide readable evidence for this student and this question.')
            if expiry:
                st.caption(t('Form expires {time}', time=ui.local_time(float(expiry))))
            if expired:
                ui.banner('Review window closed', 'Collect the workflow’s timeout response. A timed-out plan is not approved.', 'amber')
                if client and st.button(t('Collect timeout response'), type='primary', width='stretch'):
                    run_request(case['id'])
                    st.rerun()
                return
            fields = form.get('inputs') or []
            if any(f.get('type') != 'paragraph' for f in fields):
                st.error(t('This workflow has an unsupported review field. This UI supports the paragraph fields in the attached final YAML.'))
                return
            defaults = form.get('resolved_default_values') or {}
            labels = {'final_plan': 'Reviewed plan', 'record_extract': 'Record extract or verified school correction',
                      'record_reference': 'Record reference · optional', 'review_note': 'School note · optional'}
            help_text = {'final_plan': 'The exact text you approve is submitted to Dify. Chinese reports translate the reviewed original.',
                         'record_extract': 'Include the student, exam or subject, date, exact result and its scale. A number alone is insufficient.',
                         'record_reference': 'Leave blank if unavailable. This is optional for every action.',
                         'review_note': 'Optional context for the school review; this does not replace the readable record.'}
            values = {}
            with st.container(key='review_' + case['id']):
                for field in fields:
                    name = field['output_variable_name']
                    default = str(defaults.get(name) or '')
                    if not default and (field.get('default') or {}).get('type') == 'constant':
                        default = str(field.get('default', {}).get('value') or '')
                    height = 380 if name == 'final_plan' else 190 if name == 'record_extract' else 90
                    max_chars = {'record_extract': 12000, 'record_reference': 240, 'review_note': 4000}.get(name)
                    if name == 'record_reference':
                        values[name] = st.text_input(t(labels.get(name, name)), value=default, max_chars=max_chars,
                            help=t(help_text.get(name, '')), key='field_' + case['form_token'] + '_' + name)
                    else:
                        values[name] = st.text_area(t(labels.get(name, name.replace('_', ' ').capitalize())), value=default,
                            height=height, max_chars=max_chars, help=t(help_text.get(name, '')),
                            key='field_' + case['form_token'] + '_' + name)
                attested = True
                if not teacher:
                    attested = st.checkbox(t('I checked this record against the school’s source and confirm it belongs to this student.'),
                                           help=t('Required when confirming an existing record or using a supplied school record.'), key='attest_' + case['form_token'])
                    st.caption(t('The supplied record supports this request. It does not update the stored knowledge base.'))
                actions = form.get('user_actions') or []
                selected_action = ''
                with st.container(key='review_actions'):
                    for action in actions:
                        title = ACTION_LABELS.get(action['id'], str(action.get('title') or action['id']))
                        kind = 'primary' if action.get('button_style') == 'primary' else 'secondary'
                        if st.button(t(title), key='decision_' + case['form_token'] + '_' + action['id'], type=kind, width='stretch', disabled=not client or store.busy(case['id'])):
                            selected_action = action['id']
            if selected_action:
                if selected_action == 'approve_plan' and not str(values.get('final_plan') or '').strip():
                    st.warning(t('Enter the reviewed plan before approving it.'))
                elif selected_action in {'confirm_existing', 'use_school_record'} and not attested:
                    st.warning(t('Confirm that you checked the school source before accepting this evidence.'))
                else:
                    with st.status(t('Submitting your decision…'), expanded=False) as progress:
                        message = submit_review(client, store, case['id'], case['form_token'], values, selected_action,
                            st.session_state.reviewer_name or 'School reviewer',
                            progress=lambda title: progress.update(label=t(friendly_step(title))))
                        progress.update(label=t('Decision submitted' if not message else 'Request needs attention'),
                                        state='complete' if not message else 'error')
                    if message:
                        st.session_state.review_message = message
                    st.session_state.focus_epoch += 1
                    st.rerun()


def school_active_case():
    case_id = st.session_state.school_active
    if not case_id:
        return False
    case = store.get(case_id)
    if not case:
        st.session_state.school_active = ''
        return False
    if client:
        refresh_result(client, store, case_id)
        case = store.get(case_id)
    if st.button(t('← Back to requests'), key='back_inbox'):
        st.session_state.school_active = ''
        st.rerun()
    label, note, tone = display_state(case)
    if case['phase'] != 'complete':
        ui.scroll_anchor('s360-review', 'school-review-' + case_id + '-' + case['phase'] + '-' + str(st.session_state.focus_epoch))
    ui.section((case.get('student') or 'Student') + ' · ' + ui.case_ref(case),
               ui.local_time(case['created']) + ' · ' + t('Parent report: {language}', language=LANGUAGE_LABELS[case['report_language']]))
    ui.banner(label, note, tone)
    if st.session_state.get('review_message'):
        st.warning(localize_diagnostic(st.session_state.pop('review_message')))
    if case['phase'] == 'complete':
        render_report(case, school=True)
    elif case['phase'] == 'awaiting_review' and case.get('form'):
        if case.get('error'):
            st.warning(localize_diagnostic(case['error']))
        review_fields(case)
    else:
        st.markdown('**' + t('Parent’s question') + '**')
        st.write(case['question'])
        if case.get('error'):
            with st.expander(t('Connection details'), expanded=True):
                st.text(localize_diagnostic(case['error']))
                if case.get('error_status') in {401, 403} or 'connection was denied' in case['error']:
                    st.caption(t('App owner: check Dify → this app → API Access / Access API. Enable the Service API and use an app key issued for this published Workflow app. Update Streamlit Secrets and reboot after a key change.'))
        if store.busy(case_id):
            st.info(t('The workflow is processing this request. Refresh shortly to see its new state.'))
        elif case['run_id'] and client:
            if st.button(t('Reconnect / collect latest response'), type='primary'):
                run_request(case_id)
                st.rerun()
        else:
            st.caption(t('No workflow ID was received. Restore API access first. The parent can then reuse their saved question.'))
    with st.expander(t('Workflow activity')):
        st.caption(t('Workflow ID: {id}', id=case['run_id'] or t('Not received')))
        for event in case.get('events', []):
            st.caption(t(('✓ ' if event['status'] in {'succeeded', 'success'} else '· ') + t(event['title']) + ' · ' + t(event['status'])))
    if st.button(t('Refresh this request'), key='refresh_case'):
        if client:
            refresh_result(client, store, case_id, force=True)
        st.rerun()
    return True


def header(school: bool):
    with st.container(key='app_header'):
        logo, parent_tab, school_tab, language_col, options = st.columns([2.7, .95, 1.45, 1.35, .85], gap='small', vertical_alignment='center')
        with logo:
            ui.brand()
        with parent_tab:
            st.button(t('Parent'), key='mode_parent', type='secondary' if school else 'primary', width='stretch',
                      on_click=select_portal, args=('Parent',))
        with school_tab:
            st.button(t('Teacher / School'), key='mode_school', type='primary' if school else 'secondary', width='stretch',
                      on_click=select_portal, args=('Teacher / School',))
        with language_col:
            st.selectbox(t('Language'), LANGUAGES, key='ui_language', format_func=lambda x: LANGUAGE_LABELS[x],
                         label_visibility='collapsed', on_change=change_language)
        with options:
            with st.popover(t('Options'), width='stretch'):
                st.toggle(t('Auto-scroll to updates'), key='auto_scroll')
                if school and school_authenticated():
                    reviewer = st.text_input(t('Reviewer name'), value=st.session_state.reviewer_name,
                                             key='reviewer_editor', max_chars=80)
                    st.session_state.reviewer_name = reviewer.strip()
                    if settings.school_access_code:
                        st.button(t('Sign out'), on_click=sign_out, width='stretch')
    if not school or school_authenticated():
        with st.container(key='view_nav'):
            first, second, space = st.columns([1.35, 1.6, 5], gap='small', vertical_alignment='center')
            pages = ['Review inbox', 'Completed reports'] if school else ['Ask a question', 'My reports']
            active = st.session_state.school_page if school else st.session_state.parent_page
            for col, page in zip([first, second], pages):
                with col:
                    title = 'New question' if page == 'Ask a question' else page
                    st.button(t(title), key='nav_' + page.replace(' ', '_'), width='stretch',
                              type='primary' if active == page else 'secondary',
                              on_click=navigate, args=(page, school))
            with space:
                label = 'School workspace' if school else 'Parent portal'
                st.html('<div class="nav-context">' + ui.icon('school' if school else 'people',15) + escape(t(label)) + '</div>')


school = st.session_state.portal == 'Teacher / School'
ui.css(school)
ui.scroll_anchor('s360-top', 'page-' + st.session_state.portal + '-' + str(st.session_state.focus_epoch))
header(school)
ui.install_motion(st.session_state.auto_scroll)
if connection_error:
    st.error(localize_diagnostic(connection_error))
    st.caption(t('See the README to configure the separate connection file or Streamlit Cloud Secrets.'))

if school:
    if not school_authenticated():
        school_login()
    else:
        if not settings.school_access_code:
            st.info(t('The school workspace is open for demonstration. Set SCHOOL_ACCESS_CODE to require staff access.'))
        if not school_active_case():
            ui.school_header(st.session_state.reviewer_name)
            school_inbox(completed=st.session_state.school_page == 'Completed reports')
else:
    if st.session_state.parent_page == 'My reports':
        parent_history_view()
    else:
        parent_question_view()
ui.footer(school)
ui.back_to_top()

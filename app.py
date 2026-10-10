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

st.set_page_config(page_title='Student360 | Progress & support', page_icon=str(ui.ROOT / 'assets' / 'favicon.svg'),
                   layout='wide', initial_sidebar_state='expanded',
                   menu_items={'Get Help': None, 'Report a bug': None, 'About': 'Student360 · Record-based progress answers and human-reviewed learning plans.'})

LANGUAGES = ['English', 'Chinese (Simplified) 简体中文', 'Chinese (Traditional) 繁體中文']
LANGUAGE_LABELS = {'English': 'English', 'Chinese (Simplified) 简体中文': '简体中文 · Simplified Chinese',
                   'Chinese (Traditional) 繁體中文': '繁體中文 · Traditional Chinese'}
EXAMPLES = [
    ('Taylor', 'Recorded progress', 'What is Taylor’s latest recorded official IELTS result, including the date and all section scores?'),
    ('Riley', 'Check a specific result', 'What was Riley’s official PET listening score on February 28, 2026?'),
    ('Skyler', 'Request a support plan', 'Create a one-week listening support plan for Skyler based on the report and teacher feedback.'),
    ('Vishnu', 'Find a student record', 'Show the learning progress report for Vishnu.'),
]

try:
    settings = load_settings()
except (ValueError, OSError) as exc:
    st.error('The separate configuration file could not be read. Check its TOML format and restart the app.')
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
    'question': '', 'student_name': '', 'report_language': 'English', 'parent_cases': [],
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


def portal_changed():
    st.query_params['view'] = 'school' if st.session_state.portal == 'Teacher / School' else 'parent'
    st.session_state.focus_epoch += 1


def choose_example(name: str, question: str):
    st.session_state.student_name = name
    st.session_state.question = question
    st.session_state.parent_page = 'Ask a question'


def activate_parent(case: dict):
    st.session_state.parent_active = case['id']
    st.query_params['request'] = case['public_token']


def open_parent_report(case: dict):
    activate_parent(case)
    st.session_state.parent_page = 'Ask a question'
    st.session_state.focus_epoch += 1


def auth_digest() -> str:
    return hashlib.sha256(settings.school_access_code.encode('utf-8')).hexdigest()


def school_authenticated() -> bool:
    return not settings.school_access_code or hmac.compare_digest(st.session_state.school_auth, auth_digest())


def render_empty(title: str, description: str, symbol: str = 'file'):
    st.html(f'<div class="empty-state"><div class="empty-icon">{ui.icon(symbol,25)}</div><h3>{escape(title)}</h3><p>{escape(description)}</p></div>')


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
    with st.status('Preparing the request…', expanded=False) as progress:
        execute(client, store, case_id, start=start,
                progress=lambda title: progress.update(label=friendly_step(title)))
        case = store.get(case_id)
        label, _, _ = display_state(case)
        progress.update(label=label, state='error' if case['phase'] == 'interrupted' else 'complete')


def render_report(case: dict, school: bool = False):
    ui.scroll_anchor('s360-report', ('school-report-' if school else 'parent-report-') + case['id'] + '-' + str(st.session_state.focus_epoch))
    with st.container(key='report_card'):
        head, download = st.columns([3, 2], vertical_alignment='center')
        with head:
            ui.section('Student Progress Report', ui.case_ref(case) + ' · ' + ui.local_time(case['created']))
        with download:
            ui.badge(LANGUAGE_LABELS.get(case['report_language'], case['report_language']))
        st.markdown(ui.report_body(case['report']))
        st.divider()
        md, printable = st.columns(2)
        file_stub = 'Student360_' + re.sub(r'[^A-Za-z0-9_-]', '_', case.get('student') or 'Report') + '_' + case['id'][:8]
        with md:
            st.download_button('Download report · Markdown', case['report'].encode('utf-8'),
                               file_name=file_stub + '.md', mime='text/markdown', width='stretch', key='md_' + case['id'])
        with printable:
            st.download_button('Download printable report', ui.printable_report(case),
                               file_name=file_stub + '.html', mime='text/html', width='stretch', key='print_' + case['id'])
        st.caption('Printable report → Print → Save as PDF.')
    if school and case.get('review_history'):
        with st.expander('School review record'):
            for i, entry in enumerate(case['review_history']):
                st.markdown('**' + entry['reviewer'] + '** · ' + ui.local_time(entry['at']))
                st.caption('Decision: ' + entry['action'].replace('_', ' ').capitalize())
                for key, value in entry.get('inputs', {}).items():
                    if value:
                        st.markdown('**' + key.replace('_', ' ').capitalize() + '**')
                        st.text(value)
            record = {k: case[k] for k in ['question', 'report_language', 'student', 'created', 'report', 'review_history']}
            st.download_button('Download review record', json.dumps(record, ensure_ascii=False, indent=2),
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
        ui.scroll_anchor('s360-request', 'parent-request-' + case_id + '-' + case['phase'] + '-' + str(st.session_state.focus_epoch))
    else:
        ui.anchor('s360-request')
    ui.section('Your latest request', case.get('student') or 'Student progress')
    ui.banner(label, note, tone)
    ui.tracker(case)
    with st.expander('Your question & request details'):
        st.write(case['question'])
        st.caption(ui.case_ref(case) + ' · ' + ui.local_time(case['created']) + ' · ' + LANGUAGE_LABELS[case['report_language']])
    if case['phase'] == 'complete':
        render_report(case)
    elif case['phase'] == 'awaiting_review':
        teacher = case['review_kind'] == 'teacher'
        title = 'Your teacher is the next step' if teacher else 'The school will check the record'
        description = ('Your reviewed plan will appear here after the teacher’s decision.'
                       if teacher else 'More supporting information is needed. Your report will update after the school’s review.')
        render_empty(title, description, 'people' if teacher else 'search')
        st.caption('Keep this page open, or bookmark this request.')
    elif case['phase'] == 'interrupted':
        st.warning('We could not complete the connection. Your request has been retained.')
        if case['run_id'] and client:
            if st.button('Reconnect to this request', type='primary', key='parent_reconnect_' + case_id):
                run_request(case_id)
                st.rerun()
        else:
            st.caption('The connection ended before a workflow ID was received. Please send a new request using the question form.')
        with st.expander('Connection details'):
            st.write(case.get('error') or 'The report connection needs attention.')
    else:
        render_empty('Your report is being prepared', 'The school workflow is checking the available information. You can keep this page open.', 'clock')
        if case['run_id'] and client and not store.busy(case_id):
            if st.button('Continue preparing the report', key='continue_' + case_id):
                run_request(case_id)
                st.rerun()


def parent_question_view():
    ui.anchor('s360-question')
    left, right = st.columns([2.25, 1], gap='large')
    with left:
        with st.container(key='question_card'):
            ui.section('Any question or concern?', 'We are here to help.')
            with st.form('parent_question_form'):
                name, language = st.columns([1, 1.3])
                with name:
                    student = st.text_input('Student name', key='student_name', placeholder='e.g. Taylor', max_chars=60,
                                            help='You can also include the student name directly in your question.')
                with language:
                    selected_language = st.selectbox('Report language', LANGUAGES, key='report_language',
                                                      format_func=lambda x: LANGUAGE_LABELS[x])
                question = st.text_area('Your question', key='question', height=125, max_chars=1900,
                    placeholder='Ask about progress, an exam result or a support plan…')
                st.caption('Include the exam or date when relevant.')
                submitted = st.form_submit_button('Get my progress report', type='primary', width='stretch', disabled=not client)
            if submitted:
                q = question.strip()
                if not q:
                    st.warning('Please enter a question or concern.')
                else:
                    student = student.strip()
                    # Dify has question + report_language inputs, not a separate student variable.
                    # Incorporate the optional name without hiding another name in the question.
                    if student and not re.search(r'\b' + re.escape(student) + r'\b', q, re.I):
                        q = 'Question about ' + student + ': ' + q
                    names = [n for n in ['Taylor', 'Riley', 'Skyler', 'Vishnu'] if re.search(r'\b' + n + r'\b', q, re.I)]
                    alias = names[0] if len(names) == 1 else student
                    case = store.create(q, selected_language, alias)
                    st.session_state.parent_cases.append(case['id'])
                    activate_parent(case)
                    st.session_state.focus_epoch += 1
                    run_request(case['id'], start=True)
                    st.rerun()
        with st.expander('Try a demo question'):
            for name, topic, question in EXAMPLES:
                st.button(name + ' · ' + topic, key='example_' + name, width='stretch',
                          on_click=choose_example, args=(name, question))
    with right:
        ui.school_card()
        ui.process_strip()
        with st.expander('How your report is prepared'):
            st.markdown('1. Check the student’s records.\n2. Ask the school or teacher to review when needed.\n3. Share the completed report in your chosen language.')
    if st.session_state.parent_active:
        parent_live_report(st.session_state.parent_active)


def parent_history_view():
    ui.section('My reports', 'Your questions. Your completed responses.')
    cases = [store.get(i) for i in reversed(st.session_state.parent_cases)]
    cases = [c for c in cases if c]
    if not cases:
        render_empty('Your progress reports will appear here', 'Start with a question in the Parent portal. You can return to each request using its bookmarked URL.', 'book')
        return
    for case in cases:
        label, _, tone = display_state(case)
        with st.container(key='case_card_parent_' + case['id']):
            copy, action = st.columns([4, 1], vertical_alignment='center')
            with copy:
                st.html(f'<div class="mini-label">{escape(ui.case_ref(case))} · {escape(ui.local_time(case["created"],True))}</div><div class="case-title">{escape(case.get("student") or "Student progress")}</div><div class="case-question">{escape(case["question"])}</div>')
                ui.badge(label, tone)
            with action:
                st.button('Open report', key='open_parent_' + case['id'], width='stretch',
                          on_click=open_parent_report, args=(case,))


def school_login():
    school_photo, login = st.columns([1, 1.5], gap='large')
    with school_photo:
        ui.school_card(compact=True)
    with login, st.container(key='login_card'):
        ui.section('School workspace', 'Enter your school access code.')
        with st.form('school_login'):
            code = st.text_input('School access code', type='password', placeholder='Enter your access code')
            reviewer = st.text_input('Your name', placeholder='e.g. Ms. Chen', help='Included in this app’s review record.')
            submitted = st.form_submit_button('Open review workspace', type='primary', width='stretch')
        if submitted:
            if hmac.compare_digest(code, settings.school_access_code):
                st.session_state.school_auth = auth_digest()
                st.session_state.reviewer_name = reviewer.strip() or 'School reviewer'
                st.session_state.focus_epoch += 1
                st.rerun()
            else:
                st.error('The school access code did not match.')
        st.caption('For teachers and school reviewers.')


def school_case_card(case: dict):
    label, _, tone = display_state(case)
    with st.container(key='case_card_school_' + case['id']):
        copy, action = st.columns([4, 1], vertical_alignment='center')
        with copy:
            kind = 'Plan approval' if case.get('review_kind') == 'teacher' else 'Record verification'
            st.html(f'<div class="mini-label">{escape(ui.case_ref(case))} · {escape(ui.local_time(case["created"],True))}</div><div class="case-title">{escape(case.get("student") or "Student progress")} <span style="font-size:11px;font-weight:450;color:#8392a4">/ {escape(kind)}</span></div><div class="case-question">{escape(case["question"])}</div>')
            ui.badge(label, tone)
        with action:
            button = 'Review request' if case['phase'] == 'awaiting_review' else 'Open request'
            if st.button(button, key='open_school_' + case['id'], width='stretch', type='primary' if case['phase'] == 'awaiting_review' else 'secondary'):
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
        ui.stat('Record verification', len(record_cases), 'Awaiting school evidence', 'search', 'amber')
    with b:
        ui.stat('Teacher decisions', len(teacher_cases), 'Plans awaiting review', 'people', 'purple')
    with c:
        ui.stat('Completed responses', len(finished), 'Ready to read', 'file', 'green')
    ui.section('Completed reports' if completed else 'Review inbox',
               'Reports and review history.' if completed else 'Check the evidence. Review the plan. Make your decision.')
    search, filter_col = st.columns([2, 1])
    with search:
        query = st.text_input('Find a request', placeholder='Search student, question or request reference', key='school_search_' + str(completed))
    with filter_col:
        filters = ['All completed'] if completed else ['All active', 'Record verification', 'Teacher review', 'Needs attention']
        category = st.selectbox('Show', filters, key='school_filter_' + str(completed))
    selected = finished if completed else [c for c in cases if c['phase'] != 'complete']
    if category == 'Record verification':
        selected = [c for c in selected if c['phase'] == 'awaiting_review' and c.get('review_kind') != 'teacher']
    elif category == 'Teacher review':
        selected = [c for c in selected if c['phase'] == 'awaiting_review' and c.get('review_kind') == 'teacher']
    elif category == 'Needs attention':
        selected = [c for c in selected if c['phase'] == 'interrupted']
    if query.strip():
        q = query.casefold()
        selected = [c for c in selected if q in (c['student'] + ' ' + c['question'] + ' ' + ui.case_ref(c)).casefold()]
    if not selected:
        render_empty('No completed reports yet' if completed else 'The inbox is clear',
                     'Completed responses will be available here after the workflow finishes.' if completed else 'A parent request appears here when it needs school verification or a teacher decision.', 'check')
    else:
        st.caption(str(len(selected)) + ' request' + ('s' if len(selected) != 1 else '') + ' · Inbox updates automatically while open')
        for case in selected[:50]:
            school_case_card(case)
        if len(selected) > 50:
            st.caption('Showing the latest 50 matches. Use the search to narrow the inbox.')


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
                st.markdown(concise_context[:records.start()].strip())
                with st.expander('Supporting record extracts'):
                    st.markdown(concise_context[records.start():].strip())
            else:
                st.markdown(concise_context.strip())
            with st.expander('Full review instructions'):
                st.markdown(content)
    with right:
        with st.container(key='school_review'):
            ui.section('Review the learning plan' if teacher else 'Verify the school record',
                       'Edit the proposed plan before making your decision.' if teacher else 'Provide readable evidence for this student and this question.')
            if expiry:
                st.caption('Form expires ' + ui.local_time(float(expiry)))
            if expired:
                ui.banner('Review window closed', 'Collect the workflow’s timeout response. A timed-out plan is not approved.', 'amber')
                if client and st.button('Collect timeout response', type='primary', width='stretch'):
                    run_request(case['id'])
                    st.rerun()
                return
            fields = form.get('inputs') or []
            if any(f.get('type') != 'paragraph' for f in fields):
                st.error('This workflow has an unsupported review field. This UI supports the paragraph fields in the attached final YAML.')
                return
            defaults = form.get('resolved_default_values') or {}
            labels = {'final_plan': 'Reviewed plan', 'record_extract': 'Record extract or verified school correction',
                      'record_reference': 'Record reference · optional', 'review_note': 'School note · optional'}
            help_text = {'final_plan': 'The exact text you approve is submitted to Dify. Chinese reports translate the reviewed original.',
                         'record_extract': 'Include the student, exam or subject, date, exact result and its scale. A number alone is insufficient.',
                         'record_reference': 'Leave blank if unavailable. This is optional for every action.',
                         'review_note': 'Optional context for the school review; this does not replace the readable record.'}
            values = {}
            with st.form('review_' + case['id'] + '_' + case['form_token']):
                for field in fields:
                    name = field['output_variable_name']
                    default = str(defaults.get(name) or '')
                    if not default and (field.get('default') or {}).get('type') == 'constant':
                        default = str(field.get('default', {}).get('value') or '')
                    height = 380 if name == 'final_plan' else 190 if name == 'record_extract' else 90
                    max_chars = {'record_extract': 12000, 'record_reference': 240, 'review_note': 4000}.get(name)
                    if name == 'record_reference':
                        values[name] = st.text_input(labels.get(name, name), value=default, max_chars=max_chars,
                            help=help_text.get(name), key='field_' + case['form_token'] + '_' + name)
                    else:
                        values[name] = st.text_area(labels.get(name, name.replace('_', ' ').capitalize()), value=default,
                            height=height, max_chars=max_chars, help=help_text.get(name),
                            key='field_' + case['form_token'] + '_' + name)
                attested = True
                if not teacher:
                    attested = st.checkbox('I checked this record against the school’s source and confirm it belongs to this student.',
                                           help='Required when confirming an existing record or using a supplied school record.')
                    st.caption('The supplied record supports this request. It does not update the stored knowledge base.')
                actions = form.get('user_actions') or []
                selected_action = ''
                for action in actions:
                    title = str(action.get('title') or action['id'])
                    kind = 'primary' if action.get('button_style') == 'primary' else 'secondary'
                    if st.form_submit_button(title, type=kind, width='stretch', disabled=not client or store.busy(case['id'])):
                        selected_action = action['id']
            if selected_action:
                if selected_action == 'approve_plan' and not str(values.get('final_plan') or '').strip():
                    st.warning('Enter the reviewed plan before approving it.')
                elif selected_action in {'confirm_existing', 'use_school_record'} and not attested:
                    st.warning('Confirm that you checked the school source before accepting this evidence.')
                else:
                    with st.status('Submitting your decision…', expanded=False) as progress:
                        message = submit_review(client, store, case['id'], case['form_token'], values, selected_action,
                            st.session_state.reviewer_name or 'School reviewer',
                            progress=lambda title: progress.update(label=friendly_step(title)))
                        progress.update(label='Decision submitted' if not message else 'Request needs attention',
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
    if st.button('← Back to review inbox', key='back_inbox'):
        st.session_state.school_active = ''
        st.rerun()
    label, note, tone = display_state(case)
    if case['phase'] != 'complete':
        ui.scroll_anchor('s360-review', 'school-review-' + case_id + '-' + case['phase'] + '-' + str(st.session_state.focus_epoch))
    ui.section((case.get('student') or 'Student') + ' · ' + ui.case_ref(case),
               ui.local_time(case['created']) + ' · Parent report: ' + LANGUAGE_LABELS[case['report_language']])
    ui.banner(label, note, tone)
    if st.session_state.get('review_message'):
        st.warning(st.session_state.pop('review_message'))
    if case['phase'] == 'complete':
        render_report(case, school=True)
    elif case['phase'] == 'awaiting_review' and case.get('form'):
        if case.get('error'):
            st.warning(case['error'])
        review_fields(case)
    else:
        st.markdown('**Parent’s question**')
        st.write(case['question'])
        if case.get('error'):
            st.error(case['error'])
        if store.busy(case_id):
            st.info('The workflow is processing this request. Refresh shortly to see its new state.')
        elif case['run_id'] and client:
            if st.button('Reconnect / collect latest response', type='primary'):
                run_request(case_id)
                st.rerun()
        else:
            st.caption('The initial request did not return a workflow ID. Ask the parent to submit a new request.')
    with st.expander('Workflow activity'):
        st.caption('Workflow ID: ' + (case['run_id'] or 'Not received'))
        for event in case.get('events', []):
            st.caption(('✓ ' if event['status'] in {'succeeded', 'success'} else '· ') + event['title'] + ' · ' + event['status'])
    if st.button('Refresh this request', key='refresh_case'):
        if client:
            refresh_result(client, store, case_id, force=True)
        st.rerun()
    return True


def school_connection_view():
    with st.container(key='school_context'):
        ui.section('Connection & workspace', 'Connection settings are read on the server from the separate secrets configuration.')
        st.markdown('**Published workflow** · Student360')
        st.caption('Inputs: question, report_language · Output: student_progress_report')
        st.caption('The API key is never displayed in this workspace.')
        if client and st.button('Check Dify connection', type='primary'):
            try:
                info = client.info()
                if info.get('mode') != 'workflow':
                    st.error('This key belongs to another app type. Use the Student360 Workflow app key.')
                else:
                    st.success('Connected to ' + str(info.get('name') or 'the published workflow'))
            except DifyError as exc:
                st.error(client.redact(exc))
        st.divider()
        st.markdown('**Workspace storage**')
        st.write('Requests are shared between browsers connected to this Streamlit instance. Local request storage is temporary on Streamlit Community Cloud.')
        st.caption('Export completed reports or review records before redeploying. See README for the deployment and persistence details.')
        st.markdown('**School access**')
        st.write('The shared school access code controls the review workspace. Reviewer names are entered by staff and are recorded with their decisions.')


school = st.session_state.portal == 'Teacher / School'
ui.css(school)
with st.sidebar:
    ui.brand(sidebar=True)
    st.caption('YOUR WORKSPACE')
    st.radio('Choose workspace', ['Parent', 'Teacher / School'], key='portal',
             label_visibility='collapsed', on_change=portal_changed)
    st.divider()
    st.caption('NAVIGATION')
    if school:
        st.radio('School navigation', ['Review inbox', 'Completed reports', 'Connection & workspace'],
                 key='school_page', label_visibility='collapsed')
    else:
        st.radio('Parent navigation', ['Ask a question', 'My reports'], key='parent_page', label_visibility='collapsed')
    st.divider()
    st.markdown('**School & home, connected.**')
    st.toggle('Auto-scroll to updates', key='auto_scroll')
    if school and school_authenticated():
        st.divider()
        st.caption('REVIEWER')
        st.text_input('Reviewer name', key='reviewer_name', placeholder='Your name', label_visibility='collapsed')
        if settings.school_access_code and st.button('Sign out of school view', width='stretch'):
            st.session_state.school_auth = ''
            st.session_state.school_active = ''
            st.rerun()
    if not school and st.session_state.parent_active:
        st.divider()
        st.caption('Bookmark your request to return later.')

ui.install_motion(st.session_state.auto_scroll)
ui.anchor('s360-top')
ui.topbar(school)
ui.hero(school)
if connection_error:
    st.error(connection_error)
    st.caption('The README explains how to configure the separate connection file and Streamlit Cloud Secrets.')

if school:
    if not school_authenticated():
        school_login()
    else:
        if not settings.school_access_code:
            st.info('Demonstration access: the school workspace is open. Set SCHOOL_ACCESS_CODE for shared access control.')
        if st.session_state.school_page == 'Connection & workspace':
            school_connection_view()
        elif not school_active_case():
            school_inbox(completed=st.session_state.school_page == 'Completed reports')
else:
    if st.session_state.parent_page == 'My reports':
        parent_history_view()
    else:
        parent_question_view()
ui.footer(school)
ui.back_to_top()

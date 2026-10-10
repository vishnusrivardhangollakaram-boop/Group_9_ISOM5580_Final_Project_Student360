"""Workflow orchestration shared by Parent and Teacher/School views."""
from __future__ import annotations

from collections.abc import Callable
import json
import re
import time

from dify_client import DifyClient, DifyError
from store import CaseStore

REPORT_KEY = 'student_progress_report'
META_FIELDS = ('student_alias', 'route', 'request_type', 'evidence_status', 'review_status', 'change_status', 'sources')



def failed_run(case: dict) -> bool:
    """Recognize old saved plugin failures as well as the explicit terminal state."""
    return case.get('phase') == 'failed' or (case.get('phase') == 'interrupted' and (
        case.get('error_code') == 'workflow_failed' or
        any(token in case.get('error', '').lower() for token in ('plugininvokeerror', 'invokeerror', 'traceback (most recent call last)'))))


def failure_kind(message: str, status: int | None = None) -> str:
    text = str(message).lower()
    if status == 429 or any(word in text for word in ('resource_exhausted', 'quota', 'rate limit', '429')):
        return 'quota'
    if status in {401, 403} or any(word in text for word in ('api_key_invalid', 'permission_denied', 'unauthenticated')):
        return 'access'
    if any(word in text for word in ('invalid_argument', 'unsupported', 'model not found', 'not supported', 'must return student_progress_report')):
        return 'configuration'
    if any(word in text for word in ('503', 'overloaded', 'unavailable', '500 internal')):
        return 'unavailable'
    if any(word in text for word in ('plugininvokeerror', 'gemini', 'google/genai', 'invokeerror')):
        return 'model'
    return 'workflow'


def record_error(client: DifyClient, case: dict, exc: DifyError, *, terminal: bool = False):
    terminal = terminal or exc.terminal
    case['phase'] = 'failed' if terminal else 'interrupted'
    case['error'] = client.redact(exc)
    case['error_status'] = exc.status
    case['error_code'] = 'workflow_failed' if terminal else exc.code
    case['failure_kind'] = failure_kind(str(exc), exc.status)
    if terminal:
        case['form_token'], case['form'] = '', None


def apply_detail(client: DifyClient, case: dict, detail: dict) -> bool:
    """A finished run cannot be resumed. Return True for a terminal state."""
    if detail.get('status') in {'succeeded', 'success'}:
        set_result(case, detail.get('outputs'))
        return True
    if detail.get('status') in {'failed', 'stopped', 'partial-succeeded'}:
        record_error(client, case, DifyError(str(detail.get('error') or 'The workflow stopped.'), terminal=True))
        return True
    return False

def review_kind(form: dict) -> str:
    actions = {a.get('id') for a in form.get('user_actions', [])}
    return 'teacher' if 'approve_plan' in actions else 'school'


def set_result(case: dict, outputs: object):
    if isinstance(outputs, str):
        try:
            outputs = json.loads(outputs)
        except ValueError:
            outputs = {}
    if not isinstance(outputs, dict) or not str(outputs.get(REPORT_KEY) or '').strip():
        raise DifyError('The published workflow must return student_progress_report. Check the published output configuration.', terminal=True)
    case['outputs'] = outputs
    case.setdefault('metadata', {}).update({k: str(outputs[k]) for k in META_FIELDS if outputs.get(k) is not None})
    case['report'] = str(outputs[REPORT_KEY])
    case['phase'] = 'complete'
    case['error_status'], case['error_code'], case['failure_kind'] = None, '', ''
    case['form_token'], case['form'], case['error'] = '', None, ''


def update_event(case: dict, event: dict) -> str:
    name = event.get('event', '')
    data = event.get('data') or {}
    if not isinstance(data, dict):
        data = {}
    if event.get('workflow_run_id'):
        case['run_id'] = str(event['workflow_run_id'])
    if event.get('task_id'):
        case['task_id'] = str(event['task_id'])
    title = ''
    if name == 'workflow_started':
        case['run_id'] = str(event.get('workflow_run_id') or data.get('id') or case['run_id'])
        case['phase'] = 'running'
    elif name in {'node_started', 'node_finished'}:
        title = str(data.get('title') or data.get('node_title') or '')
        step = {'node': data.get('node_id', ''), 'title': title,
                'status': 'running' if name == 'node_started' else str(data.get('status') or 'succeeded')}
        # One row per node keeps reconnection snapshots from duplicating the activity record.
        existing = next((i for i, x in enumerate(case['events']) if x['node'] == step['node']), None)
        if existing is None:
            case['events'].append(step)
        else:
            case['events'][existing] = step
        case['events'] = case['events'][-70:]
        # Only status metadata is retained here; intermediate AI drafts stay out of the parent report.
        if data.get('node_id') == 'final_aggregate':
            output = data.get('outputs') or {}
            if isinstance(output, dict):
                output = output.get('output', output)
                if isinstance(output, dict):
                    case['metadata'] = {k: str(output.get(k) or '') for k in META_FIELDS}
                    if output.get('student_alias'):
                        case['student'] = str(output['student_alias'])
    elif name == 'human_input_required':
        token = data.get('form_token') or event.get('form_token')
        if not token:
            raise DifyError('The review has no API form token. Enable Web app delivery on the Dify Human Input nodes.')
        case['phase'], case['form_token'], case['form'] = 'awaiting_review', str(token), None
        case['review_kind'] = 'teacher' if data.get('node_id') == 'teacher' else 'school'
    elif name == 'workflow_paused':
        case['phase'] = 'awaiting_review'
    elif name in {'human_input_form_filled', 'human_input_form_timeout'}:
        case['phase'], case['form_token'], case['form'] = 'running', '', None
    elif name == 'workflow_finished':
        if data.get('status') not in {'succeeded', 'success'}:
            raise DifyError(str(data.get('error') or 'The workflow could not complete the report.'), terminal=True)
        set_result(case, data.get('outputs'))
    elif name == 'error':
        raise DifyError(str(event.get('message') or data.get('message') or 'The workflow reported an error.'), code=str(event.get('code') or ''), terminal=True)
    return title if name == 'node_started' else ''


def consume(client: DifyClient, store: CaseStore, case: dict, owner: str, events,
            progress: Callable[[str], None] | None = None):
    last_save = 0.0
    deadline = time.monotonic() + 540
    try:
        for event in events:
            if time.monotonic() > deadline:
                raise DifyError('This request is taking longer than expected. Reconnect to continue the same run.')
            title = update_event(case, event)
            if title and progress:
                progress(title)
            now = time.monotonic()
            if now - last_save > 0.7 or event.get('event') in {'workflow_started', 'human_input_required'}:
                store.save(case, owner)
                last_save = now
            if event.get('event') in {'workflow_finished', 'workflow_paused'}:
                break
        if case['phase'] == 'awaiting_review':
            if not case['form_token']:
                raise DifyError('The workflow paused without a review form. Reconnect or check Human Input delivery settings.')
            try:
                case['form'] = client.form(case['form_token'])
                case['review_kind'] = review_kind(case['form'])
            except DifyError as exc:
                # The review still exists even when its form cannot be fetched yet.
                case['error'] = client.redact(exc)
                store.save(case, owner)
                return
        elif case['phase'] != 'complete':
            raise DifyError('The stream ended before the report was ready. Reconnect to continue this request.')
        case['error'] = ''
        store.save(case, owner)
    finally:
        if hasattr(events, 'close'):
            events.close()


def execute(client: DifyClient, store: CaseStore, case_id: str, start: bool = False,
            progress: Callable[[str], None] | None = None):
    owner = store.acquire(case_id)
    if not owner:
        return
    case = store.get(case_id)
    try:
        if case['phase'] == 'complete' or failed_run(case):
            return
        if start and case.get('run_id'):
            start = False
        if not start and case.get('run_id'):
            # Check status before reconnecting, including old app-version failures.
            if apply_detail(client, case, client.detail(case['run_id'])):
                store.save(case, owner)
                return
            if case.get('form_token'):
                case['form'] = client.form(case['form_token'])
                case['review_kind'] = review_kind(case['form'])
                case['phase'], case['error'] = 'awaiting_review', ''
                store.save(case, owner)
                return
        case['phase'], case['error'] = 'running', ''
        case['error_status'], case['error_code'] = None, ''
        store.save(case, owner)
        events = (client.start(case['question'], case['report_language'], case['user']) if start
                  else client.resume(case['run_id'], case['user']))
        consume(client, store, case, owner, events, progress)
    except DifyError as exc:
        record_error(client, case, exc)
        store.save(case, owner)
    finally:
        store.release(case_id, owner)


def school_submission_inputs(case: dict, form: dict, inputs: dict, action: str) -> dict:
    """Attach existing request context to a school-confirmed value; preserve its text."""
    submitted = dict(inputs)
    value = str(inputs.get('record_extract') or '')
    if action != 'use_school_record' or not value.strip():
        return submitted
    content = str(form.get('form_content') or '')
    student_match = re.search(r'^\*\*Student:\*\*\s*([^\n]+)', content, re.M)
    student = student_match.group(1).strip() if student_match else str(case.get('metadata', {}).get('student_alias') or case.get('student') or '')
    requested_match = re.search(r'^\*\*Information to verify:\*\*\s*([^\n]+)', content, re.M)
    requested = requested_match.group(1).strip() if requested_match else str(case.get('question') or '')
    # Context comes from this run's review form, never an inferred score, date or unit.
    submitted['record_extract'] = (
        'School-confirmed record for this request.\n'
        f'Student: {student}\nRequested information: {requested}\n'
        'The school confirms that the following value or answer applies to the requested information above.\n'
        'School-confirmed value or answer:\n' + value
    )
    return submitted


def submit_review(client: DifyClient, store: CaseStore, case_id: str, token: str,
                  inputs: dict, action: str, reviewer: str,
                  progress: Callable[[str], None] | None = None) -> str:
    owner = store.acquire(case_id)
    if not owner:
        return 'Another reviewer is processing this request. Refresh to see the latest status.'
    case = store.get(case_id)
    try:
        if case['phase'] != 'awaiting_review' or case['form_token'] != token:
            return 'This form has already changed. Refresh the request before reviewing it.'
        form = case.get('form') or client.form(token)
        if action not in {a.get('id') for a in form.get('user_actions', [])}:
            return 'Choose one of the current review actions.'
        if form.get('expiration_time') and float(form['expiration_time']) <= time.time():
            return 'This form has expired. Collect its timeout response instead.'
        submitted_inputs = school_submission_inputs(case, form, inputs, action)
        # Teacher plans remain exact; school values travel with their existing request context.
        client.submit(token, submitted_inputs, action, case['user'])
        case['review_history'].append({'reviewer': reviewer.strip() or 'School reviewer',
            'at': time.time(), 'action': action, 'kind': case['review_kind'], 'inputs': inputs,
            'submitted_inputs': submitted_inputs,
            'original_plan': str((form.get('resolved_default_values') or {}).get('final_plan') or '')})
        case['phase'], case['form'], case['form_token'], case['error'] = 'running', None, '', ''
        store.save(case, owner)
        consume(client, store, case, owner, client.resume(case['run_id'], case['user']), progress)
        return ''
    except DifyError as exc:
        # A network error may happen after Dify accepts a decision. Require refresh/reconnect,
        # never retry the same form submission silently.
        record_error(client, case, exc)
        if exc.status in {400, 422} and case.get('form_token'):
            case['phase'] = 'awaiting_review'
        store.save(case, owner)
        return 'The decision could not be confirmed. Check the request status before submitting again.'
    finally:
        store.release(case_id, owner)


def refresh_result(client: DifyClient, store: CaseStore, case_id: str, force: bool = False):
    case = store.get(case_id)
    if not case or not case['run_id'] or case['phase'] == 'complete' or (case['phase'] == 'failed' and not force):
        return
    if not force and time.time() - case.get('last_checked', 0) < 30:
        return
    owner = store.acquire(case_id, 30)
    if not owner:
        return
    case = store.get(case_id)
    try:
        case['last_checked'] = time.time()
        detail = client.detail(case['run_id'])
        apply_detail(client, case, detail)
        store.save(case, owner)
    except DifyError:
        # A periodic read failure must not replace a valid review form or parent report.
        case['last_checked'] = time.time()
        store.save(case, owner)
    finally:
        store.release(case_id, owner)


def display_state(case: dict) -> tuple[str, str, str]:
    """Return human labels from actual run state and final report wording, never example routes."""
    phase = case['phase']
    if failed_run(case):
        reason = case.get('failure_kind') or failure_kind(case.get('error', ''), case.get('error_status'))
        if reason == 'quota':
            return 'Report service limit reached', 'Your question is saved. The school needs to check the report service quota before you try again.', 'amber'
        if reason in {'access', 'configuration'}:
            return 'Report service needs attention', 'Your question is saved. The school needs to check the report service settings before you try again.', 'red'
        return 'Report could not be completed', 'The report service stopped before completing this request. Your question is saved. You can try a new request.', 'red'
    if phase == 'awaiting_review':
        if case['review_kind'] == 'teacher':
            return 'Teacher review', 'The proposed plan is awaiting a teacher’s decision.', 'purple'
        return 'More evidence is needed', 'The school needs to check the information supporting your question.', 'amber'
    if phase in {'running', 'created'}:
        return 'Preparing your report', 'Checking the student record and supporting information.', 'blue'
    if phase == 'interrupted':
        if not case.get('run_id'):
            if case.get('error_status') in {401, 403} or 'connection was denied' in case.get('error', ''):
                return 'Request could not start', 'The report service denied access. Your question is saved; the school needs to restore the connection.', 'red'
            return 'Request could not be confirmed', 'Your question is saved, but no workflow ID was received.', 'amber'
        return 'Connection needs attention', 'Your request is retained. Reconnect to continue its workflow.', 'amber'
    report = case.get('report', '')
    review = case.get('metadata', {}).get('review_status', '')
    route = case.get('metadata', {}).get('route', '')
    if route == 'student_not_found' or any(x in report for x in ['Student record not found', '未找到学生记录', '未找到學生記錄']):
        return 'Student record not found', 'Check the student name or contact the school.', 'red'
    if route == 'clarification_required' or any(x in report for x in ['Student name clarification needed', '需要确认学生姓名', '需要確認學生姓名']):
        return 'Student name needed', 'Please ask about one student at a time.', 'amber'
    if review == 'teacher_approved' or any(x in report for x in ['Learning plan approved', '学习计划已批准', '學習計劃已批准', '**Review status:** Teacher approved', '**审核状态:** 教师已批准', '**審核狀態:** 教師已批准']):
        return 'Teacher-approved plan', 'The reviewed plan is ready to use.', 'green'
    if review == 'staff_confirmed' or any(x in report for x in ['School verified answer ready', '学校核实的答复已完成', '學校核實的答覆已完成']):
        return 'School-verified answer', 'The answer uses a record verified by the school.', 'green'
    if review in {'evidence_pending', 'answer_pending', 'timed_out', 'not_approved'} or any(x in report for x in [
        'Awaiting missing information', 'Answer awaiting another check', 'Review not completed in time', 'Plan not approved',
        '等待补充信息', '等待補充資訊', '答复等待再次检查', '答覆等待再次檢查', '计划未获批准', '計劃未獲批准',
        '审核未在时限内完成', '審核未在時限內完成']):
        return 'Further school action needed', 'Read the report for the information or review still required.', 'amber'
    return 'Progress answer ready', 'Your report is ready to read.', 'green'


def rendered_form_content(form: dict) -> str:
    return re.sub(r'\{\{#\$output\.[A-Za-z_][A-Za-z0-9_]*#\}\}', '', str(form.get('form_content') or ''))

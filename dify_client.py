"""Small standard-library Dify client. API secrets never enter rendered HTML."""
from __future__ import annotations

import json
import re
from collections.abc import Iterable, Iterator
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen


class DifyError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, code: str = ''):
        super().__init__(message)
        self.status = status
        self.code = code


def parse_sse(lines: Iterable[bytes | str]) -> Iterator[dict]:
    parts: list[str] = []
    for line in lines:
        line = (line.decode('utf-8-sig') if isinstance(line, bytes) else line).rstrip('\r\n')
        if not line:
            if parts:
                yield event_object('\n'.join(parts))
                parts.clear()
        elif line.startswith('data:'):
            parts.append(line[5:].lstrip(' '))
    if parts:
        yield event_object('\n'.join(parts))


def event_object(value: str) -> dict:
    if value.strip() in {'[DONE]', 'ping'}:
        return {'event': 'ping'}
    try:
        item = json.loads(value)
    except ValueError as exc:
        raise DifyError('The report connection returned an unreadable event. Reconnect to this request.') from exc
    if not isinstance(item, dict):
        raise DifyError('The report connection returned an unexpected event.')
    return item


class DifyClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 90):
        base_url = base_url.strip().rstrip('/')
        url = urlparse(base_url)
        if url.scheme not in {'http', 'https'} or not url.netloc or url.username or url.password:
            raise DifyError('Set DIFY_API_BASE_URL in the separate secrets configuration.')
        if not api_key.strip():
            raise DifyError('Set DIFY_API_KEY in the separate secrets configuration.')
        self.base_url, self._key, self.timeout = base_url, api_key.strip(), timeout

    def redact(self, value: object) -> str:
        text = str(value).replace(self._key, '[redacted]')
        text = re.sub(r'\bapp-[A-Za-z0-9_-]+', '[redacted]', text)
        text = re.sub(r'(?i)Bearer\s+\S+', 'Bearer [redacted]', text)
        return text[:1000]

    def request(self, method: str, path: str, body: dict | None = None, stream: bool = False):
        headers = {'Authorization': 'Bearer ' + self._key,
                   'User-Agent': 'Student360/4.0',
                   'Accept': 'text/event-stream' if stream else 'application/json'}
        data = None
        if body is not None:
            headers['Content-Type'] = 'application/json'
            data = json.dumps(body, ensure_ascii=False).encode('utf-8')
        try:
            return urlopen(Request(self.base_url + path, data=data, headers=headers, method=method),
                           timeout=self.timeout if stream else 20)
        except HTTPError as exc:
            messages = {
                401: 'The app connection was not authorized. Check the configured Dify app key.',
                403: 'Dify API access was denied. The app owner should check that this app’s Service API is enabled.',
                404: 'This workflow or review form could not be found. Check the published app and reconnect.',
                409: 'This review has already been submitted. Refresh the request to see its current status.',
                410: 'This review form has expired. Collect the latest workflow response.',
                429: 'The report service is busy. Please wait briefly and reconnect.',
            }
            # Preserve the server's reason for ALL errors, including 401/403.
            # Never display a raw HTML gateway page, response headers or request body.
            code, detail = '', ''
            try:
                payload = json.loads(exc.read(16384))
                if isinstance(payload, dict):
                    code = re.sub(r'[^a-zA-Z0-9_.-]', '', self.redact(payload.get('code') or ''))[:80]
                    detail = self.redact(payload.get('message') or '')[:500]
            except (ValueError, UnicodeError, OSError):
                pass
            finally:
                exc.close()
            message = f'HTTP {exc.code}' + (f' · {code}' if code else '')
            message += '\n' + messages.get(exc.code, 'The report service could not accept this request.')
            if detail:
                message += '\nDify response: ' + detail
            else:
                message += '\nNo readable JSON error was returned by the API or its gateway.'
            raise DifyError(message, exc.code, code) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise DifyError('The report connection was interrupted. Reconnect to the existing request to continue.') from exc

    def json(self, method: str, path: str, body: dict | None = None) -> dict:
        try:
            with self.request(method, path, body) as response:
                result = json.load(response)
        except (TimeoutError, OSError, ValueError) as exc:
            raise DifyError('The report service did not return a readable response. Refresh the current request.') from exc
        if not isinstance(result, dict):
            raise DifyError('The report service returned an unexpected response.')
        return result

    def stream(self, method: str, path: str, body: dict | None = None) -> Iterator[dict]:
        with self.request(method, path, body, stream=True) as response:
            try:
                content_type = response.headers.get('Content-Type', '')
                if 'text/event-stream' not in content_type.lower():
                    raise DifyError('The configured app did not return workflow events. Check the published Workflow app.')
                yield from parse_sse(response)
            except (TimeoutError, OSError, UnicodeError) as exc:
                raise DifyError('The report connection dropped. Reconnect to this request; its run has been retained.') from exc

    def start(self, question: str, language: str, user: str) -> Iterator[dict]:
        return self.stream('POST', '/workflows/run', {
            'inputs': {'question': question, 'report_language': language},
            'response_mode': 'streaming', 'user': user,
        })

    def resume(self, run_id: str, user: str) -> Iterator[dict]:
        query = urlencode({'user': user, 'include_state_snapshot': 'true'})
        return self.stream('GET', '/workflow/' + quote(run_id, safe='') + '/events?' + query)

    def detail(self, run_id: str) -> dict:
        return self.json('GET', '/workflows/run/' + quote(run_id, safe=''))

    def info(self) -> dict:
        return self.json('GET', '/info')

    def form(self, token: str) -> dict:
        return self.json('GET', '/form/human_input/' + quote(token, safe=''))

    def submit(self, token: str, inputs: dict, action: str, user: str) -> dict:
        # Submission is never automatically retried: the response may be lost after acceptance.
        return self.json('POST', '/form/human_input/' + quote(token, safe=''),
                         {'inputs': inputs, 'action': action, 'user': user})

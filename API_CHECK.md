# Live Dify API verification

Performed before the code changes in this update, on 10 October 2026, using the supplied Student360 app key and `https://api.dify.ai/v1`.

| Request | Observed result |
|---|---|
| `GET /info` | HTTP **200**; app name **Student 360**; mode **workflow** |
| `GET /parameters` | HTTP **200**; input variables **question** and **report_language** |
| `POST /workflows/run` with streaming | Workflow started and finished with status **succeeded** |
| Returned workflow output | **student_progress_report** |

The workflow request was: **Show the learning progress report for Vishnu.** The selected report language was **English**. The returned report said:

> We could not find a student record for Vishnu. Please check the name or contact the school to confirm the student record.

Its report details identified **Vishnu**, **Student record not found**, and **English**. This was a real API result, not a frontend simulation. No local inbox entry or mock report was added to the delivered app.

The key was read from the separate server-side secrets file. No key, authorization header or review token is reproduced here.

## Scope

This verifies API access and the published unknown-student route from the execution environment. It does not verify Taylor, Riley, Skyler, Chinese report generation, teacher form submission or the deployed Streamlit host. No unit tests, performance tests or application/browser runs were performed for this update.

The previous screenshot's 403 was not reproduced by these requests. Its original response body was discarded by the earlier frontend, so its exact historical cause remains unconfirmed. The improved client retains redacted error details if a rejection recurs.

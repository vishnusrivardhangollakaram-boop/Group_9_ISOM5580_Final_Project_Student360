# Verification — completed live scenarios

10 October 2026. The four fictional demo scenarios were tested against the configured published Student 360 Workflow at `https://api.dify.ai/v1`. The user explicitly authorized the demo requests and the Riley/Skyler review decisions. Credentials were read from the separate server-side configuration file and are not reproduced here.

## Live results

| Scenario | Observed route and action | Final outcome |
|---|---|---|
| Taylor | Retrieved the report, checked evidence and generated a factual answer automatically | Workflow succeeded. IELTS on **29 August 2026**: **overall 6.0**, Listening **5.5**, Reading **6.5**, Writing **6.0**, Speaking **6.0**; source `[Taylor-p2]` |
| Riley | Retrieved records, identified the illegible official PET listening result and paused for school review. Submitted **Request missing records**, with blank record extract and blank record reference; supplied only a demo review note | Workflow completed. **Awaiting missing information**; requested the official PET listening score for **28 February 2026**. No replacement score was supplied or reported |
| Riley — supplied answer | Entered only **152** and submitted **Use supplied school record**, with **blank reference and note**. The updated frontend attached the student and requested information already present in the review form | Workflow completed. **School verified answer ready / School confirmed the answer**. Final answer: “Riley's official PET listening score on February 28, 2026, was 152.” |
| Skyler | Produced a proposed listening plan and paused for teacher review. Replaced the draft with the edited plan below and submitted **Approve reviewed plan** | Workflow completed. **Teacher approved** and **Teacher updated the plan**. Final report contains the exact edited wording; the app retains the original AI draft in the school review record |
| Vishnu | Unknown-student branch | Workflow succeeded with **Student record not found**. No retrieval or model nodes executed |

Neither Riley nor Skyler remains paused in these live test runs. Riley's workflow completion means the school decision was recorded; it does not mean the missing score was established. That missing-records report correctly remains unresolved. A separate supplied-answer run completed successfully after the school entered the demo value `152`; it did not replace or reopen the earlier request.

### Riley plain-value fix

The first live submission of only `152` was rejected by the published workflow because it lacked record context. The frontend now attaches the student and requested information from the same Human Input form to the school-confirmed answer. It requires no reference, invented source ID or extra record text from staff.

The follow-up live run used the updated `submit_review` function with exactly `record_extract="152"`, `record_reference=""`, and `review_note=""`. It resumed the same run and user, completed successfully, and returned the value **152**. Review history retains both the exact school entry and the contextual API payload. The number is fictional test data for this demonstration, not a recovered value from the original illegible source. No knowledge-base record was changed.

This fix is in the frontend and was tested against the existing published workflow. It does not require importing the optional resilient YAML. No synthetic-record blocking check was added; school confirmation remains the human decision.

### Exact approved Skyler demo plan

Three 5-minute listening sessions on Monday, Wednesday and Friday. Note three keywords and explain one missed detail each time. Review the notes on Friday.

### Integration verified

- Live Human Input form retrieval advertised the expected field names and decision IDs.
- The review decisions were submitted through the updated application's `submit_review` function, with real Dify responses; these were not mocked API calls.
- The original run ID and user identity were retained after each decision.
- The app resumed each event stream and collected the final `student_progress_report`.
- Riley's final UI state is **Further school action needed**; Skyler's is **Teacher-approved plan**.
- A blank record reference was accepted for both Riley’s missing-record request and supplied-answer decision; the latter also used a blank note.
- Skyler's submitted wording was preserved and the original draft was retained locally by the review handler.
- The previous Gemini plugin error did not recur during these runs. Its historical underlying provider cause remains unconfirmed.
- Earlier `/info` and `/parameters` checks succeeded, identifying Student 360 as a Workflow and confirming `question` and `report_language`.

## Local checks already completed

Synthetic local checks also covered the four report states, terminal-failure handling, same-run recovery after dropped streams, retention of the review pause during a temporary form-fetch failure, and both portal renders without Streamlit exceptions. Teacher edits survived a switch to Traditional Chinese. The updated school form accepted `152`, kept its reference blank and retained the entry when switching to Traditional Chinese. Python compilation and YAML loading passed.

## Scope and limits

These live tests used the currently published English-language workflow. They do not verify the optional `Student360_Resilient.yml` by importing/publishing it, Chinese report generation, rejected plans, timeout behavior, or every possible question. No additional provider, quota or model settings were changed.

The live calls exercised the API and the application's review orchestration, not a click-through of the user's deployed Streamlit website. Browser screenshot inspection could not be completed in this environment, so final pixel-level layout and mobile-overflow checks are not claimed. No performance testing was performed.

No test databases, live event payloads, review tokens or prewritten student answers are included in the ZIP. Demo validation runs were created directly in Dify; they are not automatically added to a separately deployed Streamlit instance's local inbox. The shipped frontend uses its own saved run IDs when parents and staff make requests.

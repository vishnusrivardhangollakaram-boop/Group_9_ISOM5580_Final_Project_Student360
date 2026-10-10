# Student360

**A professional Parent portal and Teacher/School workspace for your published Dify workflow.**

Student360 turns a question into a readable progress report, brings school staff in when supporting information is missing, and keeps teacher approval for learning plans. The frontend calls your real Dify app; it does not contain prewritten student answers or select routes based on example names.

Your final API key and `https://api.dify.ai/v1` endpoint are already configured in **`.streamlit/secrets.toml`**. Both values live only in that separate server-side configuration file. Change them there for local use, or in **Streamlit Cloud → App settings → Secrets** after deployment. Python source changes are unnecessary.

### Updated visual edition

The Parent portal now uses a parent/child photo, a compact question form and your actual Christian Education school image. The Teacher/School workspace uses teacher/student imagery, the supplied school photo and a separate navy visual design. Page copy is shorter; detailed explanations and evidence excerpts are in expanders. The final Dify report content is preserved.

Smooth auto-scroll moves to a newly submitted request, an opened review, and a completed report. It runs once per update rather than on every periodic refresh. It waits while a text input is focused or you are actively scrolling, respects reduced-motion preferences, and can be turned off with **Auto-scroll to updates** in the sidebar. A **Top** button returns to the top of the page.

This version requires **Streamlit 1.65 or newer** for the documented JavaScript-enabled `st.html` enhancement. Upload the updated `requirements.txt` along with the app code. The scroll script is a trusted local asset; questions, reports, API credentials and external content are never injected into executable JavaScript.

For an existing Streamlit deployment, replace the repository’s app files, `assets/` and `requirements.txt` with this ZIP’s contents, update Cloud Secrets with the contents of this ZIP’s `.streamlit/secrets.toml`, and reboot the app after dependencies finish updating. `.streamlit/secrets.toml` remains excluded from GitHub. On a Mac, **Command + Shift + .** reveals the hidden `.streamlit` folder in Finder.

The two people photos are AI-generated decorative images of fictional models. Your supplied school photograph is included unchanged. See `MEDIA_NOTES.md` for asset paths and generation prompts.

## 1. Start locally

Use Python **3.11 or newer**. Extract the ZIP, then open a terminal in `Student360_Professional`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate` instead. Open the local URL printed by Streamlit, usually `http://localhost:8501`.

The Parent portal opens first. The sidebar switches to the Teacher/School workspace. The initial school access code is **`Student360-Review`**; change `SCHOOL_ACCESS_CODE` in the same secrets file when sharing the app. Staff enter a display name; the app records that name with each decision.

## 2. Deploy on Streamlit Community Cloud

1. Create a GitHub repository for this frontend. Upload the **contents** of `Student360_Professional` so that `app.py`, `requirements.txt`, `assets/`, the Python modules and `.streamlit/config.toml` are at the repository root. Use a private repository if preferred.
2. Keep `.streamlit/secrets.toml` out of GitHub. The included `.gitignore` excludes it, the local database and virtual environments. If uploading through GitHub’s website, manually omit `secrets.toml` because the web upload does not apply `.gitignore` for you. Hidden `.streamlit` files may not appear in a normal Finder selection; include `config.toml` explicitly.
3. Go to [Streamlit Community Cloud](https://share.streamlit.io), choose **Create app**, and select your repository and branch.
4. Set **Main file path** to **`app.py`**. If you uploaded the entire enclosing folder instead of its contents, use `Student360_Professional/app.py`.
5. Open **Advanced settings**, choose Python **3.11 or a newer supported version**, and paste the complete contents of your delivered `.streamlit/secrets.toml` into **Secrets**.
6. Deploy. The resulting `*.streamlit.app` URL opens the Parent portal. The Teacher/School workspace is available from the sidebar; `?view=school` can open that view directly.

After deployment, use **App settings → Secrets** whenever you change the API key, endpoint or school access code. Save the changes and restart/reboot the app if the current browser has an older configuration. For a local connection-file edit, save the file and rerun or restart Streamlit.

### Connection configuration

The separate file has this shape; your delivered copy already contains the actual app key:

```toml
DIFY_API_KEY = "your_student360_app_api_key"
DIFY_API_BASE_URL = "https://api.dify.ai/v1"
SCHOOL_ACCESS_CODE = "your-school-access-code"
```

`DIFY_API_BASE_URL` is the base endpoint ending in `/v1`, not the Dify web app link and not the full `/workflows/run` URL. For self-hosted Dify, use the base endpoint displayed by that app’s Access Point page. These are the Student360 **app** credentials, separate from model-provider or knowledge-base credentials.

The loader supports environment variables as overrides, Streamlit Cloud Secrets and the local file. The order is **environment → Streamlit Secrets → local file**. The endpoint and key are not cached, embedded in UI assets or exposed in a settings editor. They are read by `config.py` on each full app rerun. Changing the school access code invalidates existing school sign-ins on their next full rerun.

## 3. Match the final Dify app

The exact supplied YAML is included under `workflow/Student360_Final_Fixed.yml` as a reference. The Streamlit app calls the **published version** associated with your app API key; it does not import or execute the YAML locally.

Your final workflow contract is:

| Direction | Variable | Value |
|---|---|---|
| Input | `question` | Parent’s question, including the student name |
| Input | `report_language` | `English`, `Chinese (Simplified) 简体中文`, or `Chinese (Traditional) 繁體中文` |
| Output | `student_progress_report` | The complete formatted report in Markdown |

The optional Student name box is folded into the `question` text; the frontend does not invent another Dify input variable. Asking about multiple names can trigger Dify’s clarification branch.

In Dify, confirm the imported workflow is published, the **Find student records** retrieval node is bound to your new knowledge base, the selected model is enabled, and **Web app delivery** remains enabled on both Human Input nodes. The attached YAML has an empty `dataset_ids` list because knowledge-base bindings are installation-specific. The frontend does not change your model, retrieval or evidence rules.

The app reads the final `student_progress_report` instead of the older `answer` output. It renders only the completed report in the Parent portal. Intermediate LLM drafts, school forms, submitted evidence and form tokens stay out of the Parent view. A translated report comes from Dify’s final translation branch; the frontend does not make a separate translation-model call. The report language selector controls the report, while interface navigation remains in English.

## 4. Parent experience

- A calm teal portal with a clear question form, student name and report language.
- Honest progress states: preparing, school verification, teacher review, completed response or connection attention.
- A request timeline and final report with the backend’s sources and review wording.
- **My reports** for requests from the current browser session.
- Markdown and printable HTML downloads. Open the printable HTML in a browser and choose **Print → Save as PDF** to export a PDF.
- A private request URL, saved in the browser address bar, for returning after a review or browser refresh. Treat that URL as access to its report.

Parents cannot submit teacher approvals or school evidence from their portal. Switching to the Teacher/School workspace requires the configured school access code.

## 5. Teacher/School experience

- A navy workspace with a shared review inbox, search, filters and real request counts.
- Separate school evidence and teacher plan-review forms.
- An access-code gate, reviewer display name and school-only review history.
- Record context from the live Dify form, not a reconstructed frontend prompt.
- Editable teacher plan prefilled with Dify’s `resolved_default_values`.
- Decisions using the exact action IDs advertised by the live form.
- Completed reports, a downloadable review record and workflow activity.

### School evidence review

| Action | What the reviewer supplies | What happens in Dify |
|---|---|---|
| **Confirm existing record** | A readable extract that matches an available student record | Dify checks the extract against the retrieved record, then checks whether it answers the question |
| **Use supplied school record** | A verified, readable school record identifying the student, exam/subject, date and exact result/scale | Dify treats the school’s submission as verified evidence for this request, validates it and generates a supported answer |
| **Request missing records** | Optional note or partial information while the readable record is still unavailable | Dify returns a response explaining what remains unconfirmed |

**Record reference is optional for every action.** The UI does not require it, add a dummy reference or block a decision when it is blank. The source text establishes the evidence. A number alone, such as `200`, is not a readable student record; the backend will keep the answer pending when the submission does not establish the requested fact.

The reviewer must tick the source-verification confirmation before confirming or using a record. This records the intent of the school action; Dify still applies its own evidence checks. Supplied evidence is for this request and does **not** write back to the knowledge base. A verified school record can resolve a factual question; any resulting learning plan still follows the teacher approval branch.

### Teacher plan review

The **Reviewed plan** editor is prefilled with the live draft. Staff can edit the complete text and choose **Approve reviewed plan** or **Decline / revise plan**. The submitted plan is not stripped, reformatted or rewritten by the frontend. Your Dify workflow controls the final report formatting and optional Chinese translation. A declined or timed-out plan is not displayed as approved.

## 6. A two-browser demonstration

1. Open the deployed URL in a normal browser as a parent. Choose a demo question and submit it.
2. For a request awaiting review, keep that Parent tab open.
3. Open the same deployed app in a second browser or private window. Select **Teacher / School**, enter the school access code and a reviewer name.
4. Open the pending request, read its context, supply the evidence or edit the plan, and submit a decision.
5. Return to the Parent tab. Its report area checks the shared inbox every eight seconds and displays the final response when ready.

You can also switch views in a single browser for a compact presentation. A parent request and school review share the same server-stored Dify `user`, workflow ID and form token. The app resumes that existing workflow instead of launching a second run when a reviewer decides.

The example buttons **only populate questions**. They do not fabricate results or force routes:

| Student | Example question | Intended demonstration |
|---|---|---|
| Taylor | Latest recorded official IELTS result, date and section scores | An automatic progress answer when the available records support it |
| Riley | Official PET listening score on February 28, 2026 | A school evidence gap, then request-records or verified-record handling |
| Skyler | One-week listening support plan based on the report and feedback | A paused teacher review followed by an edited/approved or declined plan |
| Vishnu | Show the learning progress report | The workflow’s unknown-student response |

Actual routes depend on your published workflow, knowledge base and the question. For Riley, use an actual readable school record when demonstrating the supplied-evidence branch; do not treat an invented demo value as a verified result.

## 7. Deployment scope and request storage

This is a **deployable demonstration frontend** with real Dify integration. It uses server-only SQLite to share an inbox across browser sessions on a single Streamlit instance. Data survives browser refreshes while that database remains present. It is not a durable cloud database: Community Cloud restarts, redeployments or instance replacement may reset the local inbox and invalidate the bookmarked request URLs. Dify still retains its own run records subject to your Dify settings.

The queue reads the latest 200 stored requests and displays the latest 50 search matches. Keep active reviews open, export needed reports, and finish the demonstration before redeploying. On a host with persistent storage, set the optional `STUDENT360_DATABASE_PATH` to a persistent writable location. For an institutional deployment, replace the store with a managed database and add institution identity, teacher roles and verified parent-to-student access. The shared school code is a demonstration gate, not individual identity verification; reviewer display names are self-entered.

The three student aliases and the unknown-student scenario remain governed by your Dify workflow. The UI’s student-name field is not an authorization check and does not establish a parent’s right to a student’s records. Use this starter with the fictional demonstration records described in your project.

## 8. Responsiveness and connection recovery

The frontend has one third-party runtime dependency: **Streamlit**. It performs no local embeddings, model loading, runtime image generation or heavy analytics. Branding and icons are small SVG assets; photos are bundled locally and their public image data is cached. The visual system uses local CSS and system fonts. The design adapts to narrower screens and respects reduced-motion preferences.

The live Dify response uses SSE streaming. Only workflow progress is shown before completion; draft model text is not mistaken for an approved report. Parent refreshes read the local inbox every eight seconds, with an API status read throttled to at most once per 30 seconds per active request. School inbox refreshes read local state every ten seconds. API latency is determined by your Dify workflow and models; this UI does not promise a measured speedup.

Requests and review submissions are not retried automatically. Reconnection follows the existing workflow and preserves its original `user`. A server-side lease prevents two reviewers from submitting simultaneously. If a connection drops after a decision, reconnect to collect the current run state instead of resubmitting the same form. Form expiration follows the one-hour timeout configured in your YAML.

## 9. Troubleshooting

| Symptom | What to do |
|---|---|
| Configuration missing on Cloud | Paste the delivered secrets file into Advanced settings / App settings → Secrets. A local file excluded from GitHub is not automatically available on Cloud. |
| Unauthorized connection | Confirm the app API key belongs to the current published Student360 Workflow app. |
| Wrong app type | Sign in to school view → Connection & workspace → Check Dify connection. Use a Workflow app key. |
| Published workflow output mismatch | Publish the supplied final workflow; its output must be `student_progress_report`. |
| School review cannot load a form | Keep Web app delivery enabled on both Dify Human Input nodes. |
| Missing student evidence | Check the knowledge-base binding and retrieval settings in the published Dify app. |
| A bare number is not accepted as evidence | Paste the actual readable record context: student, exam/subject, date and result with scale. Leave reference blank if unavailable. |
| Report shows further school action needed | Read the actual report. The backend has not established the requested fact, the plan was declined, or the review timed out. |
| Connection dropped after submit | Open the request and choose Reconnect / collect latest response. Do not submit the same review again. |
| Review submitted directly in Dify | The Parent portal can collect the completed report through status refresh. In school view, refresh or reconnect the request to retrieve its latest form/state. |
| Request disappeared after redeploy | The local Cloud inbox was reset. Refer to the Dify run record, or submit a new demonstration request. |
| Another reviewer is processing a case | Wait for the current operation to finish and refresh. A crashed operation’s lease expires after ten minutes. |

## 10. Project layout

```text
Student360_Professional/
  app.py                       Parent and Teacher/School views
  config.py                    Separate secrets configuration loader
  dify_client.py               Server-side HTTP and SSE client
  workflow.py                  Start, pause, review, resume and final-report handling
  store.py                     Shared SQLite request inbox and submission leases
  ui.py                        Branding, status cards and report exports
  requirements.txt             Streamlit dependency
  README.md                    This guide
  assets/
    style.css                  Professional responsive visual system
    scroll.js                  Smooth scroll and Top button enhancement
    favicon.svg                Student360 mark
    parent_child.png           Parent portal photo
    teacher_students.png       Teacher/School portal photo
    christian_school.png       Your original school photo
  MEDIA_NOTES.md               Image origins and final generation prompts
  .streamlit/
    config.toml                Streamlit theme and server settings
    secrets.toml               Your configured connection values; excluded from Git
    secrets.toml.example       Placeholder configuration
  workflow/
    Student360_Final_Fixed.yml  Exact uploaded final workflow, for reference
```

`data/requests.sqlite3` is created at runtime and is excluded from Git and the delivered ZIP. No tests, benchmark files, test frameworks or model packages are included. **No tests or live API runs were performed for this build, as requested.**

Official references: [Streamlit deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app), [Cloud secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management), [Dify workflow execution](https://docs.dify.ai/en/api-reference/workflow-runs/run-workflow), [Dify Human Input flow](https://docs.dify.ai/en/api-reference/guides/human-input-flow), [Dify resumed events](https://docs.dify.ai/en/api-reference/workflow-runs/stream-workflow-events).

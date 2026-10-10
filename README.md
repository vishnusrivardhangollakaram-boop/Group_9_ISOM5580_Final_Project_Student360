# Student360

**A professional Parent portal and Teacher/School workspace for your published Dify workflow.**

Student360 turns a question into a readable progress report, brings school staff in when supporting information is missing, and keeps teacher approval for learning plans. The frontend calls your real Dify app; it does not contain prewritten student answers or select routes based on example names.

Your final API key and `https://api.dify.ai/v1` endpoint are already configured in **`.streamlit/secrets.toml`**. Both values live only in that separate server-side configuration file. Change them there for local use, or in **Streamlit Cloud → App settings → Secrets** after deployment. Python source changes are unnecessary.

### The redesigned interface

- **Parent:** a bright, clean surface with a teal/navy wordmark, an editorial portrait panel and a focused white question card. The active request opens on its own report page.
- **Teacher / School:** a distinct blue/navy palette, a staff entry page with a classroom portrait, a prominent real-school header and a compact review workspace. The original Christian Education reception image also appears as a large feature on both entry pages, with a full-photo expander.
- **Navigation:** **Parent** and **Teacher / School** switch workspaces. **New question**, **My reports**, **Review inbox** and **Completed reports** open implemented pages. **Options** contains auto-scroll, reviewer name and staff sign-out.
- **Readable type:** main text and controls use a 16–17 px scale, with larger student names and report headings. Supporting labels and dates use 13–15 px instead of the previous 8–12 px scale. Muted text has stronger contrast in both workspaces.
- **My reports:** a compact request list sits beside the selected response. The current request opens automatically, or the newest request is selected if none is active. Requests and their selected response refresh together every eight seconds. Narrow screens stack the response below a scrollable request list. The full original question remains available in its expander.
- **Tighter spacing:** reduced navigation, heading and footer gaps; removed forced blank height in the question and sign-in cards. The report view shows actual response content immediately instead of a single sparse row.
- **Rendering fixes:** no icon-only logo; decorative vectors are embedded as self-contained image sources instead of inline SVG. Primary-button labels have explicit contrast, including Streamlit's nested Markdown labels.
- **Real states:** all reports, review decisions and inbox counts come from actual requests. Requests denied before a run ID is returned do not display a preparing-response tracker. Their questions can be restored to the form without an automatic retry.

There are no decorative notifications, invented progress scores, inactive menu items or upload controls. The page background is plain. Photography stays within defined panels. Examples and detailed instructions remain in expanders.

**Auto-scroll** moves to a new request, an opened review and a completed response. It waits while you type or scroll manually, respects reduced-motion preferences, and can be disabled in **Options**. The **Top** button returns to the beginning. Periodic refreshes do not repeatedly move the page.

Dependencies are pinned to **Streamlit 1.65.0**. The trusted local scroll script uses `st.html(..., unsafe_allow_javascript=True)`. User questions, reports and credentials are never passed into executable JavaScript. Images are bundled locally. The people photographs depict fictional models; your supplied school photograph is included unchanged. See `MEDIA_NOTES.md`.

**Updating an existing deployment:** replace the repository’s Python files, `assets/`, `locales/`, `requirements.txt` and `.streamlit/config.toml` with this package, then reboot the app. Keep your working **Streamlit → App settings → Secrets** values; this layout update does not require a credential change. The delivered `.streamlit/secrets.toml` is for local use or a new deployment and must stay out of GitHub. On macOS, **Command + Shift + .** reveals `.streamlit` in Finder; on Windows, enable **View → Show → Hidden items** if needed.

## 1. Start locally

Use Python **3.11 or newer**. Extract the ZIP, then open a terminal in `Student360_Professional`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate` instead. Open the local URL printed by Streamlit, usually `http://localhost:8501`.

Your Streamlit Secrets screenshot contains the two API settings. To require staff sign-in on Cloud, also add `SCHOOL_ACCESS_CODE = "your-school-access-code"`; otherwise the app deliberately uses its labelled demonstration mode.

The Parent portal opens first. The top navigation switches to the Teacher/School workspace. The initial school access code is **`Student360-Review`**; change `SCHOOL_ACCESS_CODE` in the same secrets file when sharing the app. Staff enter a display name; the app records that name with each decision.

## 2. Deploy on Streamlit Community Cloud

1. Create a GitHub repository for this frontend. Upload the **contents** of `Student360_Professional` so that `app.py`, `requirements.txt`, `assets/`, the Python modules and `.streamlit/config.toml` are at the repository root. Use a private repository if preferred.
2. Keep `.streamlit/secrets.toml` out of GitHub. The included `.gitignore` excludes it, the local database and virtual environments. If uploading through GitHub’s website, manually omit `secrets.toml` because the web upload does not apply `.gitignore` for you. Hidden `.streamlit` files may not appear in a normal Finder selection; include `config.toml` explicitly.
3. Go to [Streamlit Community Cloud](https://share.streamlit.io), choose **Create app**, and select your repository and branch.
4. Set **Main file path** to **`app.py`**. If you uploaded the entire enclosing folder instead of its contents, use `Student360_Professional/app.py`.
5. Open **Advanced settings**, choose Python **3.11 or a newer supported version**, and paste the complete contents of your delivered `.streamlit/secrets.toml` into **Secrets**.
6. Deploy. The resulting `*.streamlit.app` URL opens the Parent portal. The Teacher/School workspace is available from the top navigation; `?view=school` can open that view directly.

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

The app reads the final `student_progress_report` instead of the older `answer` output. It renders only the completed report in the Parent portal. Intermediate LLM drafts, school forms, submitted evidence and form tokens stay out of the Parent view. A translated report comes from Dify’s final translation branch; the frontend does not make a separate translation-model call. The global language selector translates the interface immediately and sets the report language for new requests. UI translations are local; only the final report is generated/translated by Dify. See the language section below.

## Interface language and report language

The top-bar language dropdown offers **English**, **简体中文** and **繁體中文** in both workspaces. It sits outside the question form, so a selection immediately reruns the app in that language. The choice also persists in the page URL as `lang=en`, `lang=zh-CN` or `lang=zh-TW`.

- Navigation, headings, buttons, placeholders, help, validation, status messages, inbox filters, examples, review instructions and action labels use local translations from `locales/`. These cause **no translation API call**.
- A new question captures the current selection in the existing Dify `report_language` input. Its exact backend values remain `English`, `Chinese (Simplified) 简体中文` and `Chinese (Traditional) 繁體中文`.
- **The Dify YAML is unchanged.** It still produces the final `student_progress_report` in the requested language. The frontend never rewrites or translates that result.
- Changing the interface language after submitting a request changes the interface only. That existing request keeps its saved report language, shown next to its question. To request another report language, submit a new question using that language.
- Student names, questions, retrieved evidence, the editable teacher draft, staff submissions and server-provided diagnostic details retain their original content. Known template headings and instructions translate locally; original evidence passages remain intact.
- The question and review editors use native controls with stable keys outside submit-only forms, so editing does not submit a workflow action and a language switch uses synchronized widget values. A report is sent only by **Get a progress report**; a review is submitted only by an explicit decision button.
- Machine values such as action IDs, workflow routes and input/output names remain stable. The dictionaries translate display labels only.

Browser/Streamlit service menus are platform UI; they are not translated by the application. Add new app-owned wording to both JSON catalogs when customizing the interface.

## 4. Parent experience

- A clean teal-and-navy parent portal with a focused question form, student name and a global language selector.
- Honest progress states: preparing, school verification, teacher review, completed response or connection attention.
- A request tracker and final report with the backend’s sources and review wording. Human review appears in the tracker only when it occurs.
- **My reports** for requests from the current browser session, with the selected response open beside the request list. Choosing a request displays that existing run; it does not submit the question again.
- A **Download report** menu with Markdown and printable HTML downloads. Open the printable HTML in a browser and choose **Print → Save as PDF** to export a PDF.
- A private request URL, saved in the browser address bar, for returning after a review or browser refresh. Treat that URL as access to its report.

Parents cannot submit teacher approvals or school evidence from their portal. Switching to the Teacher/School workspace requires the configured school access code.

## 5. Teacher/School experience

- A navy workspace with a shared review inbox, search, filters and actual request counts.
- Separate school evidence and teacher plan-review forms.
- An access-code gate when SCHOOL_ACCESS_CODE is configured, reviewer display name and school-only review history.
- Record context from the live Dify form, not a reconstructed frontend prompt.
- Editable teacher plan prefilled with Dify’s `resolved_default_values`.
- Decisions using the exact action IDs advertised by the live form.
- Completed reports, a downloadable review record and expandable workflow activity.

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

1. Open the deployed URL in a normal browser as a parent. Expand **Explore with an example**, choose a question, then select **Get a progress report**.
2. For a request awaiting review, keep that Parent tab open.
3. Open the same deployed app in a second browser or private window. Select **Teacher / School** in the top bar, enter the school access code and a reviewer name.
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

The frontend has one third-party runtime dependency: **Streamlit**. It performs no local embeddings, model loading, runtime image generation or heavy analytics. The brand is a typographic wordmark. Decorative vector icons are encoded as image sources; photos are bundled locally and their public image data is cached. The visual system uses local CSS and system fonts. The design adapts to narrower screens and respects reduced-motion preferences.

The live Dify response uses SSE streaming. Only workflow progress is shown before completion; draft model text is not mistaken for an approved report. Parent refreshes read the local inbox every eight seconds, with an API status read throttled to at most once per 30 seconds per active request. School inbox refreshes read local state every ten seconds. API latency is determined by your Dify workflow and models; this UI does not promise a measured speedup.

Requests and review submissions are not retried automatically. Reconnection follows the existing workflow and preserves its original `user`. A server-side lease prevents two reviewers from submitting simultaneously. If a connection drops after a decision, reconnect to collect the current run state instead of resubmitting the same form. Form expiration follows the one-hour timeout configured in your YAML.

## 9. Troubleshooting

### HTTP 403: “The app connection was denied”

**Previously completed API check:** the supplied app key succeeded against Dify before this typography and layout revision. Both metadata endpoints returned HTTP 200, and the Vishnu workflow completed successfully. Your screenshot uses the correct Secrets variable names and base endpoint. The historical 403 explanation below remains useful if a deployment still returns it; it does not mean API access is currently disabled. This revision does not repeat the API check.

The screenshots show the old frontend's message for **HTTP 403**, before a workflow ID was received. The request was denied at the API boundary: the Vishnu/student-not-found branch was not reached. This is not a retrieval/chunking setting or evidence-gap result.

The earlier client discarded the server response for 403, so its exact reason cannot be recovered from that screenshot. A disabled Service API is one cause documented by Dify; a deployment access policy or upstream gateway can also reject a request. The updated client retains the HTTP status, JSON error code and redacted message. It never renders raw gateway HTML, request headers or credentials.

1. Open the **published Student360 Workflow app in Dify** and its **API Access / Access API** page. Confirm the **Service API is enabled**.
2. Confirm the API key was issued for **that same app**. If you imported the YAML into a different app, use a key belonging to the new app. Publishing an app alone does not establish that the Service API is enabled.
3. In **Streamlit Community Cloud → App settings → Secrets**, use the current app key and `DIFY_API_BASE_URL = "https://api.dify.ai/v1"`. This is the API base URL, not a share/web-app URL. Save and reboot the app after a credential change.
4. Return to the retained request and choose **Use this question again**, then **Get a progress report**. This is an explicit new submission. The app never silently repeats a workflow start.
5. If the API still rejects it, expand **Connection details** to see the new status/code/message. If it says no readable JSON was returned, the app cannot identify the exact gateway policy; provide the HTTP status and time to the Dify administrator/support.

For a timeout before the first workflow event, a run may already exist even though this app received no ID. Check Dify Logs before resubmitting. A known run ID continues through **Reconnect to this request** instead.

See [Dify's disabled-Service-API explanation](https://docs.dify.ai/en/cli/troubleshooting) and [API setup](https://docs.dify.ai/en/api-reference/guides/get-started).

### Other issues


| Symptom | What to do |
|---|---|
| Configuration missing on Cloud | Paste the delivered secrets file into Advanced settings / App settings → Secrets. A local file excluded from GitHub is not automatically available on Cloud. |
| Unauthorized connection (401) | Confirm the app API key belongs to the current published Student360 Workflow app. |
| Wrong app type | Check the app type in Dify. This frontend requires a published Workflow app key. |
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
  ui.py                        Portal imagery, typography, status and report exports
  i18n.py                      Local UI language and review-label helpers
  locales/
    zh-CN.json                 Simplified Chinese interface messages
    zh-TW.json                 Traditional Chinese interface messages
  API_CHECK.md                 Recorded live API verification results
  requirements.txt             Streamlit dependency
  README.md                    This guide
  assets/
    style.css                  Responsive parent and school design system
    scroll.js                  Smooth scroll and Top button enhancement
    favicon.svg                Student360 mark
    parent_portrait.png        New Parent portal portrait
    school_portrait.png        New staff entry portrait
    christian_school.png       Your original school photo
  MEDIA_NOTES.md               Image origins and final generation prompts
  .streamlit/
    config.toml                Streamlit theme and server settings
    secrets.toml               Your configured connection values; excluded from Git
    secrets.toml.example       Placeholder configuration
  workflow/
    Student360_Final_Fixed.yml  Exact uploaded final workflow, for reference
```

`data/requests.sqlite3` is created at runtime and is excluded from Git and the delivered ZIP. No tests, benchmark files, test frameworks or model packages are included. **Live API checks were performed before this update, as explicitly requested:** `/info` and `/parameters` returned HTTP 200, and a real Vishnu workflow completed successfully with a student-record-not-found report. See `API_CHECK.md`. No unit tests, performance tests or application/browser runs were performed. This confirms the API key and published unknown-student route from the execution environment; it does not verify every student/review route or the deployed Streamlit host.

Official references: [Streamlit deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app), [Cloud secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management), [Dify workflow execution](https://docs.dify.ai/en/api-reference/workflow-runs/run-workflow), [Dify Human Input flow](https://docs.dify.ai/en/api-reference/guides/human-input-flow), [Dify resumed events](https://docs.dify.ai/en/api-reference/workflow-runs/stream-workflow-events).

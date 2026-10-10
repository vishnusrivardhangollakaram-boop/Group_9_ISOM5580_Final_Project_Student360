# What to replace

1. Replace the app’s Python files, `assets/`, `locales/`, `requirements.txt` and `.streamlit/config.toml` in your repository.
2. Keep your working Streamlit Cloud Secrets. Do not upload `.streamlit/secrets.toml` to GitHub.
3. Reboot the Streamlit app.
4. To enable backend LLM retries and exact English approved-plan formatting, import and publish `workflow/Student360_Resilient.yml` in Dify, confirming the knowledge base and provider configuration. The original YAML remains included for comparison.

The Riley screenshot is a backend model-plugin failure, not a missing-evidence response. This package fixes how failures are represented and recovered from; it does not claim to repair the remote provider. Use the retained provider error details in Dify to resolve persistent model failures. `/info` and `/parameters` checks passed. Live checks for all four fictional scenarios are now complete, including Riley’s missing-records action and Skyler’s edited-plan approval; see `API_CHECK.md`. The reviewed runs finished successfully. A further Riley test found that the published workflow rejected a plain numeric school answer. This version fixes the frontend handoff by attaching the student and requested information from the current review form. A live retest with only `152`, a blank reference and a blank note completed with **School confirmed the answer**. The school’s original text is retained in review history. Deploy the updated frontend to enable this fix; no Dify republish is required for it.

All report, review and request pages now use a photographic backdrop. The school background is the actual supplied Christian Education image. Content remains in readable panels, with the existing large typography and responsive column layout.

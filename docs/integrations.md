# Integration setup

## OpenAI

Set `OPENAI_API_KEY` and optionally `OPENAI_MODEL` in the root `.env`. Agent execution and employee chat return a clear configuration error when the key is absent. Task output is validated before it can be marked complete.

## Google Sheets

1. Enable the Google Sheets API in a Google Cloud project.
2. Create a service account and share the target spreadsheet with its service-account email as an editor.
3. Put the service-account JSON in a protected file outside source control and set `GOOGLE_SERVICE_ACCOUNT_JSON` to that file path (or to the JSON string for hosted secret settings).
4. Set `GOOGLE_SPREADSHEET_ID`; optionally set `GOOGLE_SHEET_TAB` (default `Tasks`).
5. Use Integrations → Sync tasks now. Automatic task changes also attempt synchronization. Database writes remain authoritative if Sheets is unavailable.

The sheet includes a Task ID key to update existing rows instead of appending duplicates.

## Email reports

Configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_FROM_EMAIL`; then set the report recipient, time, time zone, and schedule in Settings. The scheduler records provider errors. A report is marked sent only after the SMTP server accepts it.

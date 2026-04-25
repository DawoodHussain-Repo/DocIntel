# DocIntel Frontend

Next.js 16 frontend for the DocIntel MVP. It connects directly to the FastAPI backend for uploads, document analysis, clause rewrites, PDF report downloads, and grounded SSE chat.

## Current flow

- `app/page.tsx`: upload a real PDF or DOCX and show recent documents.
- `app/workspace/page.tsx`: load live summary, risk score, extracted fields, evidence-backed review items, rewrite modal, and document chat.
- `app/report/page.tsx`: render a print-friendly report preview and download the backend-generated PDF.
- `lib/api.ts`: single client for `/api/upload_contract`, `/api/analyze_document`, `/api/rewrite_clause`, `/api/chat/stream`, and `/api/report_pdf`.
- `lib/file-store.ts`: cache uploaded files locally for in-app PDF preview and keep recent document metadata in browser storage.

## Run locally

```bash
npm install
npm run dev
```

Set the backend URL in `.env.local` when needed:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## Validation

```bash
npm run typecheck
npm run build
```

`npm run build` can fail in the current Windows sandbox with `spawn EPERM`; `npm run typecheck` is the reliable validation command inside this environment.

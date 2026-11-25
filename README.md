# Techma Mail

A small, self-hostable email API with a Resend-style `POST /emails` endpoint. It accepts a Bearer API key and sends through an SMTP provider. It is intentionally a focused sending service, not a full Resend clone.

## Features

- `POST /emails` with `from`, `to`, `subject`, `text`, `html`, `cc`, `bcc`, `reply_to`, `headers`, and `tags` fields (unknown fields are ignored for basic compatibility).
- Bearer API-key authentication using constant-time comparison.
- SMTP settings supplied through environment variables.
- Optional sender-domain allowlist.
- Recipient and request-size limits.
- `/health` health check.
- Render Blueprint included.

Not implemented: attachments, scheduled sends, batch endpoints, templates, inbound email, webhooks, domains management, idempotency, delivery-event tracking, and Resend's full error contract. The API is compatible with the basic send-email call shape, not every Resend feature.

## Local development

Python 3.11+ recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with SMTP details and a long random API_KEY
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In development, interactive docs are at `http://127.0.0.1:8000/docs`.

Generate a strong API key locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Render deployment

1. Push this project to a Git repository you control.
2. In Render, create a new Blueprint and select the repository. Render reads `render.yaml`.
3. Add the SMTP values in the Render environment settings. Use credentials from an SMTP relay/provider that explicitly permits transactional email.
4. Set `ALLOWED_FROM_DOMAINS` to the exact sender domain(s), comma-separated.
5. Deploy and wait for `/health` to pass.
6. Copy the generated `API_KEY` from the service environment. Keep it server-side; never expose it in browser JavaScript or a public mobile app.

The included `render.yaml` uses the `starter` plan as a conservative deployment default; choose a plan based on the provider's current limits and your expected usage.

## SMTP settings

- Port 587: normally `SMTP_USE_TLS=false`, `SMTP_START_TLS=true`.
- Port 465: normally `SMTP_USE_TLS=true`, `SMTP_START_TLS=false`.
- `SMTP_FROM_EMAIL` documents the primary sender address. The API's `from` field is passed through after optional domain allowlist validation. Your SMTP provider must authorize that sender/domain.

**Important:** This service does not bypass domain ownership or sender verification. Configure SPF and DKIM records exactly as your SMTP provider specifies, and publish a DMARC policy. Without authorized sender infrastructure, messages may be rejected or marked as spam.

## API usage

```bash
curl -X POST "$MAIL_API_URL/emails" \
  -H "Authorization: Bearer $MAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "Bamesie Book <mail@example.com>",
    "to": ["client@example.net"],
    "subject": "Welcome to Bamesie Book",
    "text": "Your account is ready.",
    "html": "<p>Your account is ready.</p>"
  }'
```

A successful response contains an email ID:

```json
{
  "id": "email_...",
  "object": "email",
  "from": "Bamesie Book <mail@example.com>",
  "to": ["client@example.net"],
  "created_at": "2026-01-01T12:00:00+00:00"
}
```

### Bamesie Book integration

I inspected `Techma2004/bamesie-book` on its `main` branch. Its mailer is `src/lib/email.ts`: it sends a `fetch()` request directly to `https://api.resend.com/emails` with `Authorization: Bearer ${RESEND_API_KEY}` and a JSON body containing `from`, `to`, `subject`, `text`, and optional `html`. The sender is read from `EMAIL_FROM`. `src/lib/auth.ts` uses the same `RESEND_API_KEY` + `EMAIL_FROM` pair to decide whether email verification is enabled.

That means the service already accepts the payload Bamesie Book sends. To switch providers, the cleanest small change is to make the endpoint configurable while keeping the existing key and sender variable names:

```ts
const emailApiUrl = process.env.EMAIL_API_URL || "https://api.resend.com";

const response = await fetch(`${emailApiUrl.replace(/\\/$/, "")}/emails`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ from, to, subject, text, ...(html ? { html } : {}) }),
});
```

Then configure Bamesie Book's server-side environment:

```env
RESEND_API_KEY=<your Techma Mail API key>
EMAIL_FROM="Bamesie Book <mail@your-authorized-domain>"
EMAIL_API_URL=https://your-service.onrender.com
```

`EMAIL_API_URL` is the only new Bamesie Book setting. Existing code defaults to Resend if it is absent. The `RESEND_API_KEY` name is retained purely to avoid a wider application refactor; it will contain your Techma Mail key after cutover.

**Important issue found during inspection:** `src/lib/email.ts` currently logs provider/network errors but does not throw. Better Auth callbacks can therefore appear to succeed even when an email was rejected. Before relying on email verification or password-reset emails in production, change the mailer to throw on non-2xx responses and network failures, then test both flows end to end. Do not switch the production URL until Techma Mail has passed a real SMTP test.

## Security notes

- Use HTTPS in production.
- Keep the API key and SMTP password in Render's secret environment variables.
- Never commit `.env`.
- Rotate the API key if exposed.
- Keep this API private to trusted server-side applications.
- Start with low sending volume and follow your SMTP provider's acceptable-use and rate limits.
- SMTP acceptance is not proof of inbox delivery. Add provider delivery events/monitoring if you later need delivery, bounce, or complaint status.

# Bamesie Book integration notes

Inspected repository: `Techma2004/bamesie-book`, branch `main`.

## Existing implementation

- `src/lib/email.ts` sends `POST https://api.resend.com/emails`.
- Auth header: `Authorization: Bearer ${RESEND_API_KEY}`.
- JSON body: `from`, `to`, `subject`, `text`, and optional `html`.
- Sender: `EMAIL_FROM`.
- `src/lib/auth.ts` enables email verification when both `RESEND_API_KEY` and `EMAIL_FROM` are configured.

Techma Mail supports this basic request shape and the same Bearer authentication scheme.

## Minimal application change

In `src/lib/email.ts`, add a configurable base URL:

```ts
const emailApiUrl = process.env.EMAIL_API_URL || "https://api.resend.com";
```

Replace the hard-coded fetch URL:

```ts
const response = await fetch(`${emailApiUrl.replace(/\/$/, "")}/emails`, {
```

Keep the existing key and payload names. This preserves the current default Resend behavior and lets the deployment switch by environment configuration.

Set these variables in the Bamesie Book hosting environment:

```env
RESEND_API_KEY=<Techma Mail API key>
EMAIL_FROM="Bamesie Book <mail@your-authorized-domain>"
EMAIL_API_URL=https://your-techma-mail-service.onrender.com
```

No changes to Better Auth's callback payloads are required.

## Reliability fix recommended before production

The existing `sendEmail()` catches provider errors and only logs them. It resolves normally even after a non-2xx response or network failure. Change it to throw when the provider rejects the message or cannot be reached. This allows Better Auth's caller to observe the failure instead of silently treating a failed send as success.

Test:
1. Password reset email.
2. Signup verification email.
3. Invalid Techma Mail API key.
4. SMTP provider unavailable/rejecting.
5. Valid delivery to an inbox you control.

Do not switch production traffic until those tests pass.

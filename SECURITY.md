# Security Policy

## Supported versions

This repository is a reference release. Security fixes land on the latest tagged version first.

## Report a vulnerability

Please do **not** open public issues for security vulnerabilities.

Instead:
1. Email the maintainer address you plan to publish with.
2. Include reproduction steps, affected endpoints, and risk summary.
3. If the issue involves OpenClaw automation, include the webhook mapping or hook configuration used.

## Secure defaults in this release

- Server binds to `127.0.0.1` by default.
- Read APIs are local-only by default; write APIs require a bearer token.
- Write APIs enforce a lightweight per-IP rate limit.
- Ticket text and directives are treated as untrusted input.
- The UI renders dynamic text with `textContent` and never injects user strings as raw HTML.
- OpenClaw webhook examples use a fixed default session key and leave request session-key overrides disabled.

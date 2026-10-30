# Security and privacy

This repository is a standalone, single-user local application. It is not a hardened public multi-user service.

## Publication boundary

The initial public snapshot has fresh Git history and includes reusable source, generic configuration templates, synthetic tests, and optional synthetic demo goals. It excludes the source deployment's Git history, private profiles, databases, attachments, personal records, credentials, OAuth tokens, environment files, hosting identity, and cloud bindings.

The repository is scanned with Gitleaks and a public-tree check before publication. Scanning reduces risk but is not a guarantee that arbitrary future contributions contain no secrets.

## Runtime boundary

- Servers bind to loopback by default.
- Tenant IDs isolate queries but do not authenticate users.
- Optional API-token protection is a shared local service credential. The web proxy does not provide end-user login.
- SQLite and browser storage are not encrypted by this application. Use operating-system protections for local private data.
- Live AI, push, and OAuth integrations communicate with external providers when enabled.
- Do not publish an instance without providing authentication, HTTPS, secret management, backups, and an appropriate access model.

Never post a real key or private record in a public issue. Report a vulnerability through the repository's private security reporting option if available; otherwise open an issue containing only a high-level request for a private reporting channel. If a credential is exposed, revoke it with the provider; deleting a commit does not revoke it.

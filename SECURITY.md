# Security Policy

## Supported versions

This project is pre-1.0 (`0.0.0`) and under active development. Only the latest commit on `main` receives security fixes; there are no maintained release branches yet.

## Reporting a vulnerability

Please report security issues privately rather than opening a public issue.

- Preferred: open a [private vulnerability report](https://github.com/karbassi/GEDCOM/security/advisories/new) via GitHub Security Advisories.
- Alternatively, contact the maintainer through the email on the [karbassi](https://github.com/karbassi) GitHub profile.

Please include enough detail to reproduce the issue — affected version or commit, a minimal input document or model, and the observed versus expected behavior. You can expect an initial acknowledgement within a few days. Once a fix is available, the advisory will be published with credit to the reporter unless you prefer to remain anonymous.

## Scope

This library is a **writer only** — it serializes a data model to GEDCOM 7 text and never parses untrusted GEDCOM input. The most relevant concerns are therefore around the CLI's handling of authoring documents (YAML/JSON/TOML) and GEDZIP (`.gdz`) packaging:

- Untrusted authoring documents — parsing behavior and resource consumption.
- Path handling when reading authoring inputs or writing `.ged`/`.gdz` output.
- Any way crafted input could cause the writer to emit non-conformant or unsafe output.

Reading or parsing arbitrary GEDCOM files is permanently out of scope (see the README), so parser-class vulnerabilities do not apply to this project.

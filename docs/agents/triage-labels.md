# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual status strings used in this repo's issue tracker.

| Label in mattpocock/skills | Status in our tracker | Meaning                                  |
| -------------------------- | --------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`        | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`          | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`     | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`     | Requires human implementation            |
| `wontfix`                  | `wontfix`             | Will not be actioned                     |

Because issues are local markdown files, the "status" is recorded as a `Status:` line near the top of each issue file. When a skill mentions a role (e.g. "apply the AFK-ready triage label"), write the corresponding status string from this table.

Edit the right-hand column to match whatever vocabulary you actually use.

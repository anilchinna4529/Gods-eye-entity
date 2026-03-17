# Scope (Gods-eye-entity v1)

This project is a local-first **Security Operations Command Center** for **authorized defensive operations**:

- Asset inventory and basic topology mapping
- Vulnerability/config findings tracking
- Alert queue and acknowledgement workflow
- Threat intel ingestion (file-based, local)
- Automation playbooks (allowlisted defensive actions only)
- Full audit trail for user actions and automated executions

## Explicitly Out Of Scope

The v1 implementation does **not** include:

- Exploit automation (e.g., Metasploit control, exploit chains)
- Password cracking, credential harvesting, or bypass techniques
- Persistence, lateral movement, or "gain access" workflows
- Any tooling intended to compromise systems

If future requirements include offensive security testing, it must be handled in a separate, explicitly authorized project with strict governance. This repository remains defensive-only.


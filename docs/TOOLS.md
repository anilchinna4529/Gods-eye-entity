# Tooling Guide (Defensive-Only)

This repository is a **defensive SOC command center**. It does not bundle or automate exploit chains, password cracking, or "gain access" workflows.

## What's Included Here (Docker Compose)

From `Gods-eye-entity/`:

- Core app stack: `docker compose up --build`
- Optional observability (Prometheus + Grafana stubs): `docker compose --profile observability up --build`
- Optional SIEM/search (OpenSearch + Dashboards stubs): `docker compose --profile siem up --build`

OpenSearch endpoints (when the `siem` profile is enabled):

- OpenSearch: `http://localhost:9200`
- Dashboards: `http://localhost:5601`

OpenSearch initial admin password:

- Set `OPENSEARCH_INITIAL_ADMIN_PASSWORD` in `.env` (see `infra/env.example`).

## Tools That Require Separate Install/Hosts

Many tools in `Requirments1.txt` are best run outside this repo, for example:

- Network sensors (Zeek/Suricata/Snort/Arkime/ntopng): typically need a Linux host/VM with access to real network interfaces (SPAN/TAP) or PCAPs.
- GUI tools (Wireshark, Autopsy, Maltego): install on the analyst workstation.
- Full distributions (Security Onion, REMnux): deploy as dedicated VMs/hosts.
- Commercial/SaaS (Qualys, Splunk, ThreatConnect, Nessus, Nexpose): require licensing/accounts; integrate via APIs/exported reports.

## Out Of Scope For This Repo

We do not add or automate offensive tooling (for example password cracking/brute-force or exploit-focused tools). If you need authorized penetration testing, keep it in a separate, explicitly governed lab/project.

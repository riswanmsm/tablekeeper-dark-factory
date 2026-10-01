# 🏭 Dark Factory: Autonomous Multi-Agent Software Factory

> **WeAreDevelopers x BAND: Dark Factory AI Hackathon** (Sept 26 – Oct 5, 2026)  
> **Platform:** BAND Desktop (`band-sdk`)  
> **Topology:** 3 Seats (`@planner`, `@builder`, `@verifier`) with 100% Generic Mandates  

---

## 🚀 Quick Start

### 1. Configure Credentials
Copy `.env.example` to `.env` and fill in your BAND agent IDs and model API keys:
```bash
cp .env.example .env
```

### 2. Launch the Agent Seats in BAND Desktop
Spin up all three seats using Docker Compose:
```bash
docker compose up --build
```
The seats will connect to your BAND Desktop room and report ready for task dispatch.

### 3. Dispatch a Stage Brief
In your BAND Desktop room, paste the stage specification:
```
@planner Begin Stage 1 for [tablekeeper | pocketful]. Here is the official specification: [...]
```
The factory will autonomously decompose, implement, verify, and package the stage without human intervention.

### 4. Audit Factory Compliance
Run the automated self-grader at any point:
```bash
python3 ../.agents/skills/dark-factory-hackathon/scripts/audit_dark_factory.py --dir .
```

---

## 🏛️ Factory Architecture & Seat Roles

- **`@planner` (Lead Architect & Coordinator):** Translates human stage briefs into strict API contracts, data models, and concurrency invariants. Marks stages approved only after 100% verification pass.
- **`@builder` (Implementation Engineer):** Writes production backend/frontend code in `/workspace/stage-N/`, enforces atomic locking and idempotency key persistence, and packages containers.
- **`@verifier` (Independent QA & Concurrency Gate):** Audits deliverables with automated contract tests, Playwright headless UI checks, and parallel race-condition stress suites.

---

## 📦 Directory Structure

```
dark-factory/
├── mandates/
│   ├── planner.md         # Generic mandate for @planner
│   ├── builder.md         # Generic mandate for @builder
│   └── verifier.md        # Generic mandate for @verifier
├── workspace/             # Shared volume mounted into agent containers
│   ├── stage-1/           # Standalone Stage 1 service
│   ├── stage-2/           # Standalone Stage 2 service
│   ├── stage-3/           # Standalone Stage 3 service
│   ├── stage-4/           # Standalone Stage 4 service
│   └── room_export.json   # Exported BAND Desktop room chat log
├── FACTORY.md             # Complete architecture, costs & failure recovery report
├── docker-compose.yml     # Local BAND seat runner configuration
├── run_seat.py            # BAND SDK seat connector script
└── README.md
```

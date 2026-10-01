.PHONY: help run test test-offline seats audit clean

help:
	@echo "=================================================================="
	@echo "  🏭 DARK FACTORY (AUTONOMOUS MULTI-AGENT SOFTWARE FACTORY)       "
	@echo "=================================================================="
	@echo "  make run           - One-click launch Stage 1 in isolated .venv"
	@echo "  make test          - Run Stage 1 concurrency & contract test suite"
	@echo "  make test-offline  - Verify Stage 1 container with --network none"
	@echo "  make seats         - Launch BAND Desktop Agent Seats (Docker Compose)"
	@echo "  make audit         - Run automated Hackathon Compliance Auditor"
	@echo "  make clean         - Remove temporary artifacts and caches"
	@echo "=================================================================="

run:
	@cd stage-1 && ./run.sh

test:
	@cd stage-1 && make test

test-offline:
	@cd stage-1 && ./run_offline_test.sh

seats:
	@echo "🤖 Spinning up BAND agent seats (@planner, @builder, @verifier)..."
	@docker compose up --build

audit:
	@python3 ../.agents/skills/dark-factory-hackathon/scripts/audit_dark_factory.py --dir .

clean:
	@cd stage-1 && make clean

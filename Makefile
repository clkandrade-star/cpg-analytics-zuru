.PHONY: setup test extract dbt-run dbt-test dbt-docs dashboard lint

setup:
	python -m venv .venv
	.venv/bin/pip install -r src/requirements.txt
	@echo "Activate with: source .venv/bin/activate  (Windows: .venv\\Scripts\\activate)"

test:
	pytest tests/ -v

extract:
	python src/extract_off.py
	python src/extract_zuru.py

dbt-run:
	cd dbt && dbt run

dbt-test:
	cd dbt && dbt test

dbt-docs:
	cd dbt && dbt docs generate && dbt docs serve

dashboard:
	streamlit run streamlit_app.py

lint:
	ruff check src/ tests/ streamlit_app.py

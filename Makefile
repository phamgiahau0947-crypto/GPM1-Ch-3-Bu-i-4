# Đề án 03 — VaR, ES & Backtesting. Trên Windows không có `make`: dùng `python scripts/run_all.py <target>`.
PY ?= python

.PHONY: all data run test report lint notebook fresh clean

all:
	$(PY) scripts/run_all.py all

data:
	$(PY) scripts/run_all.py data

run:
	$(PY) scripts/run_all.py run

report:
	$(PY) scripts/run_all.py report

test:
	$(PY) -m pytest -q tests

lint:
	ruff check src tests scripts dashboard

notebook:
	jupyter nbconvert --to notebook --execute notebooks/00_full_analysis.ipynb --output 00_full_analysis.ipynb --ExecutePreprocessor.timeout=1800

fresh:
	$(PY) scripts/run_all.py all --fresh

clean:
	rm -rf data/processed/* outputs/tables/* outputs/figures/* outputs/logs/*

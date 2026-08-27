.PHONY: backend simulator frontend test dataset rul-data train verify

backend:
	uvicorn backend.app.main:app --reload

simulator:
	python simulator/run_simulator.py

frontend:
	cd frontend && npm run dev

test:
	pytest -q

dataset:
	python simulator/generate_dataset.py

rul-data:
	python simulator/generate_rul_dataset.py

train:
	python ai/train_all.py

verify:
	python scripts/verify_backend.py

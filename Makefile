.PHONY: install fetch sync validate mock-all clean docker-build

install:
	pip install -e .

fetch:
	dataeng-cli fetch --source uniprot --query "insulin" --output ./data/raw

sync:
	dataeng-cli sync --source uniprot --since 2026-01-01

validate:
	dataeng-cli validate ./data/processed --format json --output result.json

mock-demo:
	dataeng-cli fetch --source uniprot --query "aspirin" --mock
	dataeng-cli sync --source uniprot --mock
	dataeng-cli validate ./data/processed --format json

clean:
	rm -rf ./data result.json *.egg-info build

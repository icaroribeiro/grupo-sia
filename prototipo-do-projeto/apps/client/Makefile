# Common tasks.
set-env:
	.\scripts\set_env.bat

format:
	ruff check --select I --fix . \
	ruff format .

# Client tasks.
run-client:
	python scripts/run_client.py

build-container:
	docker build -f Dockerfile.client -t client-image .

startup-container:
	docker run --name client-container --env-file .env -p 8501:8501 client-image

shutdown-container:
	docker stop client-container && docker rm client-container

remove-image:
	docker rmi client-image

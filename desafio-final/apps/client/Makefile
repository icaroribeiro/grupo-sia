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
	docker build -f Dockerfile.client -t client-app-image .

startup-container:
	docker run --name client-app-container --env-file .env -p 8501:8501 client-app-image

shutdown-container:
	docker stop client-app-container && docker rm client-app-container

remove-image:
	docker rmi client-app-image
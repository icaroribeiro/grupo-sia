# General tasks.
set-env:
	.\scripts\set_env.bat

format:
	ruff check --select I --fix . \
	ruff format .

# Client tasks.
run-client:
	uv run scripts/run_client.py

# Container tasks.
# build-container:
# 	docker build -f Dockerfile.client -t client-image .

# startup-container:
# 	docker run -d --name client-container --env-file .env -p 8000:8000 -v client_data:/data/client client-image

# shutdown-container:
# 	docker stop client-container && docker rm client-container

# remove-image:
# 	docker rmi client-image

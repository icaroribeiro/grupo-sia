format:
	ruff check --select I --fix . \
	ruff format .

run-app:
	streamlit run streamlit_app.py

build-container:
	docker build -f Dockerfile.multi-stage -t streamlit-app-image .

startup-container:
	docker run --name streamlit-app-container --env-file .env -p 8501:8501 streamlit-app-image

shutdown-container:
	docker stop streamlit-app-container && docker rm streamlit-app-container

remove-image:
	docker rmi streamlit-app-image

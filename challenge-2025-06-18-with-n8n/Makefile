build-container:
	docker build -f Dockerfile -t n8n-workflow-image .

startup-container:
	docker run --name n8n-workflow-container -v .\:/home/node/.n8n -p 5678:5678 n8n-workflow-image

shutdown-container:
	docker stop n8n-workflow-container && docker rm n8n-workflow-container

remove-image:
	docker rmi n8n-workflow-image
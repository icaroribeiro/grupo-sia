# Desafio 18-06-2025

Grupo SIA (Soluções Inteligentes Autônomas)

## Take-home Assignment

- [Introduction](#introduction)
- [How to configure the application?](#how-to-configure-the-application)
- [How to run the application?](#how-to-run-the-application)
- [How to use the application?](#how-to-use-the-application)
- [Deployment](#deployment)

## Introduction

This application consists in a application with the purpose of being an AI agent that processes invoices developed with [**Python**](https://www.python.org/) using [**Streamlit**](https://github.com/streamlit/streamlit) and [**CrewAI**](https://github.com/crewAIInc/crewAI) frameworks that can be run in a [**Docker**](https://www.docker.com/) container.

## How to configure the application?

The application can be configured using your OpenAI API key or your Gemini API key. (It doesn't need to set up both of them to use the application.)

To do that, follow the step below:

1. Configure .env file:

Rename the **.env.example** file to **.env** file and assign one of the previous keys to the associated environment variables.

2. Configure .streamlit/secrets.toml file:

Rename the **.streamlit/secrets.toml.example** file to **.streamlit/secrets.toml** file and assign one of the previous keys to the associated environment variables.

## How to run the application?

The application can be run using a Docker container with commands from a Makefile file or even a docker-compose.yml file.

1. Run using Makefile file

A **Makefile** file was created as a single entry point containing a set of instructions to run the application using Docker containers via commands in the terminal.

To run the application, execute the commands:

1. Create a container image from a Dockerfile and a build context:

```
make build-container
```

2.  Create and start a new Docker container from previous image:

```
make startup-container
```

To finish the applications, execute the command:

```
make shutdown-container
```

2.  Run using docker-compose.yml file

A **docker-compose.yml** file was created to run the application as an alternative to using the Makefile file.

To run the application, execute the command:

```
docker-compose up --build -d streamlit-app
```

To finish the applications, execute the command:

```
docker-compose down -v --rmi local streamlit-app
```

## How to use the application?

After running the application successfully, open the browser and access the URL: http://localhost:8501/.

Then, submit a zip file with invoices to be sent to the application by clicking on the 'Submit .zip file' button.

After that, ask a question and click on the 'Get answer' button.

Wait for the processing and check the answer.

If you want to ask a new question, just write it in the text box and click on the 'Get answer' button again.

## Deployment

The application was deployed with [**Render**](https://render.com/) and can be accessed through the link: https://grupo-sia-desafio-18-06-2025.onrender.com/

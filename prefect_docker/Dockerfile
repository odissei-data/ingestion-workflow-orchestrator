FROM thomasve/prefect_docker_base:latest

EXPOSE 4200

COPY ./scripts/start-prefect.sh .

RUN apt-get update && apt-get install git -y

COPY .gitmodules .
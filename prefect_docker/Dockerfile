FROM thomasve/prefect_docker_base:latest

EXPOSE 4200

COPY ./scripts .

RUN apt-get update && apt-get install git -y

COPY .gitmodules .
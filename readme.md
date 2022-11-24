# Prefect + Docker

A small project which contains two working parts:

- Prefect
- Docker

## Versioning and dependency management

- Python: Poetry
- Environment vars: .env
- Version control: git

## Deployment

Put relevant stuff in the .env file and map in docker-compose. Remember; mapping in traefik is also possible, but you need to explicitly declare this as environment variables before traefik plays nice with them.

## Setup & structure

This project doesn't do jack by design; this is intended to give you a working Prefect instance with minimum hassle. All the magic happens in the submodule in `scripts`. By initializing this; you will have a copy of the top level files included in the scripts repository.

- Scripts are responsible for (1) declaring top level variables for a given Flow. These flows are then fed to (imported) Tasks.
- Scripts is responsible for housing (through a lower level of submodules) the correct Tasks. These Tasks perform atomic functions.

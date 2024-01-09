FROM thomasve/prefect-base:latest

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

WORKDIR /
COPY scripts ./scripts
COPY resources ./resources
WORKDIR /scripts

CMD ["/usr/bin/supervisord"]

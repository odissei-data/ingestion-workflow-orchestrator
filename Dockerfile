FROM thomasve/prefect-base:latest

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

WORKDIR /
COPY scripts ./scripts
COPY resources ./resources
WORKDIR /scripts
COPY entrypoint.sh /usr/local/bin
RUN chmod +x /usr/local/bin/entrypoint.sh
COPY entrypoint-agent.sh /usr/local/bin
RUN chmod +x /usr/local/bin/entrypoint-agent.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

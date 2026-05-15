FROM jenkins/ssh-agent:jdk21

USER root

# Get uv binaries from the docker image
COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /uvx /bin/

# Install Docker CLI and dependencies
RUN apt-get update && apt-get install -y \
    jq git curl unzip ca-certificates gnupg \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && echo "\
Types: deb \n\
URIs: https://download.docker.com/linux/debian \n\
Suites: $(. /etc/os-release && echo "$VERSION_CODENAME") \n\
Components: stable \n\
Architectures: $(dpkg --print-architecture) \n\
Signed-By: /etc/apt/keyrings/docker.asc" > /etc/apt/sources.list.d/docker.sources \
    && apt-get update && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]


FROM jenkins/ssh-agent:jdk21

USER root

# Install python and dependencies
RUN apt update && apt install -y \
    python3 python3-pip python3-venv jq \
    git curl unzip ca-certificates gnupg \
    && rm -rf /var/lib/apt/lists/*

# Add Docker's official GPG key
RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to apt sources
RUN echo "\
Types: deb \n\
URIs: https://download.docker.com/linux/debian \n\
Suites: $(. /etc/os-release && echo "$VERSION_CODENAME") \n\
Components: stable \n\
Architectures: $(dpkg --print-architecture) \n\
Signed-By: /etc/apt/keyrings/docker.asc" > /etc/apt/sources.list.d/docker.sources

# Install Docker CLI 
RUN apt update && apt install -y docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]


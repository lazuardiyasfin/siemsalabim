#!/bin/bash
set -e

DOCKER_SOCKET="/var/run/docker.sock"
DOCKER_GROUP="docker"
JENKINS_USER="jenkins"

if [ -S ${DOCKER_SOCKET} ]; then
    DOCKER_GID=$(stat -c %g ${DOCKER_SOCKET})

    EXISTING_GROUP=$(getent group ${DOCKER_GID} | cut -d: -f1)

    if [ -z ${EXISTING_GROUP} ]; then
        groupadd -g ${DOCKER_GID} ${DOCKER_GROUP}
    fi
    
    usermod -aG ${DOCKER_GROUP} ${JENKINS_USER}
fi

exec setup-sshd "$@"
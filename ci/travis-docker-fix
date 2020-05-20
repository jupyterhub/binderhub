#!/bin/bash
set -eu

# This is a workaround to an issue caused by the existence of a docker registry
# mirror in our CI environment. Without this fix that removes the mirror,
# chartpress fails to realize the existence of already built images and rebuilds
# them.
#
# ref: https://github.com/moby/moby/issues/39120
sudo cat /etc/docker/daemon.json
echo '{"mtu": 1460}' | sudo dd of=/etc/docker/daemon.json
sudo systemctl restart docker
docker ps -a

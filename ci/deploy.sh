#!/bin/bash
set -eu
docker login -u "${DOCKER_USERNAME}" -p "${DOCKER_PASSWORD}"
openssl aes-256-cbc -K $encrypted_c6b45058ffe8_key -iv $encrypted_c6b45058ffe8_iv -in travis.enc -out travis -d
set -x
chmod 0400 travis
export GIT_SSH_COMMAND="ssh -i ${PWD}/travis"
cd helm-chart
./build.py --commit-range "${TRAVIS_COMMIT_RANGE}" --push --publish-chart

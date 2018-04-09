#!/bin/bash
set -ex
# install nsenter if missing (needed by kube on trusty)
if ! which nsenter; then
  curl -L https://github.com/minrk/git-crypt-bin/releases/download/trusty/nsenter > nsenter
  echo "5652bda3fbea6078896705130286b491b6b1885d7b13bda1dfc9bdfb08b49a2e  nsenter" | shasum -a 256 -c -
  chmod +x nsenter
  sudo mv nsenter /usr/local/bin/
fi

# install kubectl, minikube
# based on https://blog.travis-ci.com/2017-10-26-running-kubernetes-on-travis-ci-with-minikube
echo "installing kubectl"
curl -Lo kubectl https://storage.googleapis.com/kubernetes-release/release/v${KUBE_VERSION}/bin/linux/amd64/kubectl
chmod +x kubectl
mv kubectl bin/

echo "installing minikube"
curl -Lo minikube https://storage.googleapis.com/minikube/releases/v${MINIKUBE_VERSION}/minikube-linux-amd64
chmod +x minikube
mv minikube bin/

echo "starting minikube"
sudo $PWD/bin/minikube start --vm-driver=none --kubernetes-version=v${KUBE_VERSION}
minikube update-context

echo "waiting for kubernetes"
JSONPATH='{range .items[*]}{@.metadata.name}:{range @.status.conditions[*]}{@.type}={@.status};{end}{end}'
until kubectl get nodes -o jsonpath="$JSONPATH" 2>&1 | grep -q "Ready=True"; do
  sleep 1
done

echo "installing helm"
curl -ssL https://storage.googleapis.com/kubernetes-helm/helm-v2.7.2-linux-amd64.tar.gz \
  | tar -xz -C bin --strip-components 1 linux-amd64/helm
chmod +x bin/helm
helm init

echo "waiting for tiller"
until helm version; do
    sleep 1
  done
helm version

echo "installing git-crypt"
curl -L https://github.com/minrk/git-crypt-bin/releases/download/0.5.0/git-crypt > bin/git-crypt
echo "46c288cc849c23a28239de3386c6050e5c7d7acd50b1d0248d86e6efff09c61b  bin/git-crypt" | shasum -a 256 -c -
chmod +x bin/git-crypt

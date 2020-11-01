#!/bin/bash
set -ex

mkdir -p bin

# install conntrack for minikube with k8s 1.18.2
# install libgnutls28-dev for pycurl
sudo apt-get update
sudo apt-get -y install conntrack libgnutls28-dev

echo "installing minikube"
curl -Lo minikube https://storage.googleapis.com/minikube/releases/v${MINIKUBE_VERSION}/minikube-linux-amd64
chmod +x minikube
mv minikube bin/

echo "starting minikube with RBAC"
sudo CHANGE_MINIKUBE_NONE_USER=true $PWD/bin/minikube start --vm-driver=none --kubernetes-version=v${KUBE_VERSION}
minikube update-context

echo "installing kubectl"
curl -Lo kubectl https://storage.googleapis.com/kubernetes-release/release/v${KUBE_VERSION}/bin/linux/amd64/kubectl
chmod +x kubectl
mv kubectl bin/

echo "installing helm ${HELM_VERSION}"
curl -sf https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 \
  | DESIRED_VERSION=v${HELM_VERSION} bash

echo "waiting for kubernetes"
JSONPATH='{range .items[*]}{@.metadata.name}:{range @.status.conditions[*]}{@.type}={@.status};{end}{end}'
until kubectl get nodes -o jsonpath="$JSONPATH" 2>&1 | grep -q "Ready=True"; do
  sleep 1
done
kubectl get nodes

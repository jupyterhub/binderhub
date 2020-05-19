#!/bin/bash
set -ex

mkdir -p bin

# install conntrack for minikube with k8s 1.18.2
# install libgnutls28-dev for pycurl
# install socat for helm2
sudo apt-get update
sudo apt-get -y install conntrack libgnutls28-dev socat

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

echo "starting minikube with RBAC"
sudo CHANGE_MINIKUBE_NONE_USER=true $PWD/bin/minikube start --vm-driver=none --kubernetes-version=v${KUBE_VERSION}
minikube update-context

echo "waiting for kubernetes"
JSONPATH='{range .items[*]}{@.metadata.name}:{range @.status.conditions[*]}{@.type}={@.status};{end}{end}'
until kubectl get nodes -o jsonpath="$JSONPATH" 2>&1 | grep -q "Ready=True"; do
  sleep 1
done
kubectl get nodes

# create clusterrolebinding needed for RBAC
kubectl create clusterrolebinding add-on-cluster-admin --clusterrole=cluster-admin --serviceaccount=kube-system:default

echo "installing helm"
curl -ssL https://storage.googleapis.com/kubernetes-helm/helm-v${HELM_VERSION}-linux-amd64.tar.gz \
  | tar -xz -C bin --strip-components 1 linux-amd64/helm
chmod +x bin/helm

kubectl --namespace kube-system create sa tiller
kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller
helm init --service-account tiller

echo "waiting for tiller"
kubectl --namespace=kube-system rollout status --watch deployment/tiller-deploy

echo "installing git-crypt"
curl -L https://github.com/minrk/git-crypt-bin/releases/download/0.5.0/git-crypt > bin/git-crypt
echo "46c288cc849c23a28239de3386c6050e5c7d7acd50b1d0248d86e6efff09c61b  bin/git-crypt" | shasum -a 256 -c -
chmod +x bin/git-crypt

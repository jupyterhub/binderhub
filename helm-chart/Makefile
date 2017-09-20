VERSION=$(shell git rev-parse --short HEAD)
IMAGE_PREFIX=jupyterhub/k8s

.PHONY: images push-images package-chart

images:
	python build.py build

push-images:
	python build.py build --push

package-chart: .PHONY
	helm package binderhub

VERSION=$(shell git rev-parse --short HEAD)
IMAGE_PREFIX=jupyterhub/k8s
PUSH_IMAGES=no
BUILD_ARGS=

images: build-images push-images
build-images: build-image/hub build-image/singleuser-sample build-image/binderhub
push-images: push-image/hub push-image/singleuser-sample push-image/binderhub

build-image/%:
	cd images/$(@F) && \
	docker build -t $(IMAGE_PREFIX)-$(@F):v$(VERSION) . $(BUILD_ARGS)

push-image/%:
	docker push $(IMAGE_PREFIX)-$(@F):v$(VERSION)

package-chart:
	helm package jupyterhub

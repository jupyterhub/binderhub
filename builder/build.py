"""Contains build of a docker image from a git repository."""

import json
import threading

from kubernetes import client, config, watch


class Build:
    """
    Represents a build of a git repository into a docker image.

    Behavior
    --------
    This ultimately maps to a single pod on a kubernetes cluster. Many
    different build objects can point to this single pod and perform
    operations on the pod. The code in this class needs to be careful and take
    this into account.
    
    For example, operations a Build object tries might not succeed because
    another Build object pointing to the same pod might have done something
    else. This should be handled gracefully, and the build object should
    reflect the state of the pod as quickly as possible.

    'name'
    ------
    The 'name' should be unique and immutable since it is used to
    sync to the pod. The 'name' should be unique for a 
    (git_url, ref, builder_image) tuple, and the same tuple should correspond
    to the same 'name'. This allows use of the locking provided by k8s API
    instead of having to invent our own locking code.
    """
    def __init__(self, q, api, name, namespace, git_url, ref, builder_image,
                 image_name, push_secret):
        self.q = q
        self.api = api
        self.git_url = git_url
        self.ref = ref
        self.builder_image = builder_image
        self.name = name
        self.namespace = namespace
        self.image_name = image_name
        self.push_secret = push_secret

    def get_spec(self):
        """Get a specification for image to be built from config."""
        return {
            "kind": "Build",
            "apiVersion": "v1",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace
            },
            "spec": {
                # Blank, we don't use this for anything
                "triggeredBy": [],
                "source": {
                    "type": "Git",
                    "git": {
                        "uri": self.git_url,
                        "ref": self.ref
                    }
                },
                "strategy": {
                    "type": "Source",
                    "sourceStrategy": {
                        "from": {
                            "kind": "DockerImage",
                            "name": self.builder_image,
                        }
                    }
                },
                "output": {
                    # This isn't actually used, we have to set status.outputDockerImageReference
                    # But we need to set this otherwise builder doesn't even attempt to push
                    "to": {
                        "kind": "DockerImage",
                        "name": self.image_name
                    },
                    # This also isn't used - we mount the secret manually in our pod spec
                    # Is here for completeness
                    "pushSecret": {
                        "name": self.push_secret
                    }
                }
            },
            "status": {
                "outputDockerImageReference": self.image_name
            }

        }

    def progress(self, kind, obj):
        """Put the current action item into the queue for execution."""
        self.q.put_nowait({'kind': kind, 'payload': obj})

    def submit(self):
        """Submit a image spec to openshift's s2i and wait for completion """
        self.pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name=self.name,
                labels={"name": self.name}
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        image="openshift/origin-sti-builder:v1.5.0",
                        name="builder",
                        env=[client.V1EnvVar(name="BUILD", value=json.dumps(self.get_spec()))],
                        volume_mounts=[
                            client.V1VolumeMount(mount_path="/var/run/docker.sock", name="docker-socket"),
                            client.V1VolumeMount(mount_path="/root/.docker", name='docker-push-secret')
                        ],
                    )
                ],
                volumes=[
                    client.V1Volume(
                        name="docker-socket",
                        host_path=client.V1HostPathVolumeSource(path="/var/run/docker.sock")
                    ),
                    client.V1Volume(
                        name='docker-push-secret',
                        secret=client.V1SecretVolumeSource(secret_name=self.push_secret)
                    )
                ],
                restart_policy="Never"
            )
        )

        try:
            ret = self.api.create_namespaced_pod(self.namespace, self.pod)
        except client.rest.ApiException as e:
            if e.status == 409:
                # Someone else created it!
                pass
            else:
                raise

        w = watch.Watch()
        try:
            for f in w.stream(self.api.list_namespaced_pod, self.namespace, label_selector="name={}".format(self.name)):
                if f['type'] == 'DELETED':
                    self.progress('pod.phasechange', 'Deleted')
                    return
                self.pod = f['object']
                self.progress('pod.phasechange', self.pod.status.phase)
                if self.pod.status.phase == 'Succeeded':
                    self.cleanup()
                elif self.pod.status.phase == 'Failed':
                    self.cleanup()
        finally:
            w.stop()

    def stream_logs(self):
        """Stream a pod's log."""
        for line in self.api.read_namespaced_pod_log(
                self.name,
                self.namespace,
                follow=True,
                _preload_content=False):

            self.progress('log', line.decode('utf-8'))

    def cleanup(self):
        """Delete a kubernetes pod."""
        try:
            self.api.delete_namespaced_pod(
                name=self.name,
                namespace=self.namespace,
                body=client.V1DeleteOptions(grace_period_seconds=0))
        except client.rest.ApiException as e:
            if e.status == 404:
                # Is ok, someone else has already deleted it
                pass
            else:
                raise

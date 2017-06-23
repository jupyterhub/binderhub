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
    (git_url, ref) tuple, and the same tuple should correspond
    to the same 'name'. This allows use of the locking provided by k8s API
    instead of having to invent our own locking code.
    """
    def __init__(self, q, api, name, namespace, git_url, ref, builder_image,
                 image_name, push_secret):
        self.q = q
        self.api = api
        self.git_url = git_url
        self.ref = ref
        self.name = name
        self.namespace = namespace
        self.image_name = image_name
        self.push_secret = push_secret
        self.builder_image = builder_image

    def get_cmd(self):
        """Get the cmd to run to build the image"""
        cmd = [
            'jupyter-repo2docker',
            self.git_url,
            '--ref', self.ref,
            '--image', self.image_name,
            '--no-clean', '--no-run', '--json-logs',
        ]

        if self.push_secret:
            cmd.append('--push')


    def progress(self, kind, obj):
        """Put the current action item into the queue for execution."""
        self.q.put_nowait({'kind': kind, 'payload': obj})

    def submit(self):
        """Submit a image spec to openshift's s2i and wait for completion """
        volume_mounts = [
            client.V1VolumeMount(mount_path="/var/run/docker.sock", name="docker-socket")
        ]
        volumes=[client.V1Volume(
            name="docker-socket",
            host_path=client.V1HostPathVolumeSource(path="/var/run/docker.sock")
        )]
        if self.push_secret:
            volume_mounts.append(client.V1VolumeMount(mount_path="/root/.docker", name='docker-push-secret'))
            volumes.append(client.V1Volume(
                name='docker-push-secret',
                secret=client.V1SecretVolumeSource(secret_name=self.push_secret)
            ))

        self.pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name=self.name,
                labels={"name": self.name}
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        image=self.builder_image,
                        name="builder",
                        args=self.get_cmd(),
                        image_pull_policy='Always',
                        volume_mounts=volume_mounts,
                    )
                ],
                volumes=volumes,
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

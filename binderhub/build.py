"""
Contains build of a docker image from a git repository.
"""

import json
from urllib.parse import urlparse

from kubernetes import client, watch
from tornado.ioloop import IOLoop
from tornado.log import app_log


class Build:
    """Represents a build of a git repository into a docker image.

    This ultimately maps to a single pod on a kubernetes cluster. Many
    different build objects can point to this single pod and perform
    operations on the pod. The code in this class needs to be careful and take
    this into account.

    For example, operations a Build object tries might not succeed because
    another Build object pointing to the same pod might have done something
    else. This should be handled gracefully, and the build object should
    reflect the state of the pod as quickly as possible.

    ``name``
        The ``name`` should be unique and immutable since it is used to
        sync to the pod. The ``name`` should be unique for a
        ``(git_url, ref)`` tuple, and the same tuple should correspond
        to the same ``name``. This allows use of the locking provided by k8s
        API instead of having to invent our own locking code.

    """
    def __init__(self, q, api, name, namespace, git_url, ref, builder_image,
                 image_name, push_secret, memory_limit, docker_host):
        self.q = q
        self.api = api
        self.git_url = git_url
        self.ref = ref
        self.name = name
        self.namespace = namespace
        self.image_name = image_name
        self.push_secret = push_secret
        self.builder_image = builder_image
        self.main_loop = IOLoop.current()
        self.memory_limit = memory_limit
        self.docker_host = docker_host

    def get_cmd(self):
        """Get the cmd to run to build the image"""
        cmd = [
            'jupyter-repo2docker',
            '--ref', self.ref,
            '--image', self.image_name,
            '--no-clean', '--no-run', '--json-logs',
        ]

        if self.push_secret:
            cmd.append('--push')

        if self.memory_limit:
            cmd.append('--build-memory-limit')
            cmd.append(str(self.memory_limit))

        # git_url comes at the end, since otherwise our arguments
        # might be mistook for commands to run.
        # see https://github.com/jupyter/repo2docker/pull/128
        cmd.append(self.git_url)

        return cmd

    def progress(self, kind, obj):
        """Put the current action item into the queue for execution."""
        self.main_loop.add_callback(self.q.put, {'kind': kind, 'payload': obj})

    def submit(self):
        """Submit a image spec to openshift's s2i and wait for completion """
        volume_mounts = [
            client.V1VolumeMount(mount_path="/var/run/docker.sock", name="docker-socket")
        ]
        docker_socket_path = urlparse(self.docker_host).path
        volumes = [client.V1Volume(
            name="docker-socket",
            host_path=client.V1HostPathVolumeSource(path=docker_socket_path)
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
                labels={
                    "name": self.name,
                    "component": "binderhub-build",
                },
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        image=self.builder_image,
                        name="builder",
                        args=self.get_cmd(),
                        image_pull_policy='Always',
                        volume_mounts=volume_mounts,
                        resources=client.V1ResourceRequirements(
                            limits={'memory': self.memory_limit},
                            requests={'memory': self.memory_limit}
                        )
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
            for f in w.stream(
                    self.api.list_namespaced_pod,
                    self.namespace,
                    label_selector="name={}".format(self.name)):
                if f['type'] == 'DELETED':
                    self.progress('pod.phasechange', 'Deleted')
                    return
                self.pod = f['object']
                self.progress('pod.phasechange', self.pod.status.phase)
                if self.pod.status.phase == 'Succeeded':
                    self.cleanup()
                elif self.pod.status.phase == 'Failed':
                    self.cleanup()
        except Exception as e:
            app_log.exception("Error in watch stream")
            raise
        finally:
            w.stop()

    def stream_logs(self):
        """Stream a pod's log."""
        for line in self.api.read_namespaced_pod_log(
                self.name,
                self.namespace,
                follow=True,
                _preload_content=False):
            # verify that the line is JSON
            line = line.decode('utf-8')
            try:
                json.loads(line)
            except ValueError:
                # log event wasn't JSON.
                # use the line itself as the message with unknown phase.
                # We don't know what the right phase is, use 'unknown'.
                # If it was a fatal error, presumably a 'failure'
                # message will arrive shortly.
                app_log.error("log event not json: %r", line)
                line = json.dumps({
                    'phase': 'unknown',
                    'message': line,
                })

            self.progress('log', line)

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

class FakeBuild(Build):
    """
    Fake Building process to be able to work on the UI without a running Minikube.
    """
    def submit(self):
        self.progress('pod.phasechange', 'Running')
        return

    def stream_logs(self):
        import time
        time.sleep(3)
        for phase in ('Pending', 'Running', 'Succeed', 'Building'):
            self.progress('log',
                json.dumps({
                    'phase': phase,
                    'message': f"{phase}...\n",
                })
            )
        for i in range(5):
            time.sleep(1)
            self.progress('log',
                json.dumps({
                    'phase': 'unknown',
                    'message': f"Step {i+1}/10\n",
                })
            )
        self.progress('pod.phasechange', 'Succeeded')
        self.progress('log', json.dumps({
                'phase': 'Deleted',
                'message': f"Deleted...\n",
             })
        )

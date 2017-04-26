import json
import threading

from kubernetes import client, config, watch

class Build:
    def __init__(self, q, api, name, namespace, git_url, ref, builder_image, image_name, push_secret):
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
        self.q.put_nowait({'kind': kind, 'payload': obj})

    def submit(self):
        """
        Submits the given build spec and waits for 
        """
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
                self.already_exists = True
            else:
                raise

        w = watch.Watch()
        try:
            for f in w.stream(self.api.list_namespaced_pod, self.namespace, label_selector="name={}".format(self.name)):
                self.pod = f['object']
                self.progress('pod.phasechange', self.pod.status.phase)
                if self.pod.status.phase == 'Succeeded':
                    return True
                elif self.pod.status.phase == 'Failed':
                    return False
        finally:
            w.stop()

    def stream_logs(self):
        for line in self.api.read_namespaced_pod_log(
                self.name,
                self.namespace,
                follow=True,
                _preload_content=False):

            self.progress('log', line.decode('utf-8'))

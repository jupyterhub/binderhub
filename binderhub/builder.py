"""
Handlers for working with version control services (i.e. GitHub) for builds.
"""

import asyncio
import hashlib
import json
import re
import string
import time
from http.client import responses

import docker
import escapism
from prometheus_client import Counter, Gauge, Histogram
from tornado import gen
from tornado.httpclient import HTTPClientError
from tornado.ioloop import IOLoop
from tornado.iostream import StreamClosedError
from tornado.log import app_log
from tornado.queues import Queue
from tornado.web import Finish, authenticated

from .base import BaseHandler
from .build import Build, ProgressEvent
from .utils import KUBE_REQUEST_TIMEOUT

# Separate buckets for builds and launches.
# Builds and launches have very different characteristic times,
# and there is a cost to having too many buckets in prometheus.
BUILD_BUCKETS = [60, 120, 300, 600, 1800, 3600, 7200, float("inf")]
LAUNCH_BUCKETS = [2, 5, 10, 20, 30, 60, 120, 300, 600, float("inf")]
BUILD_TIME = Histogram(
    "binderhub_build_time_seconds",
    "Histogram of build times",
    ["status"],
    buckets=BUILD_BUCKETS,
)
LAUNCH_TIME = Histogram(
    "binderhub_launch_time_seconds",
    "Histogram of launch times",
    ["status", "retries"],
    buckets=LAUNCH_BUCKETS,
)
BUILD_COUNT = Counter(
    "binderhub_build_count",
    "Counter of builds by repo",
    ["status", "provider", "repo"],
)
LAUNCH_COUNT = Counter(
    "binderhub_launch_count",
    "Counter of launches by repo",
    ["status", "provider", "repo"],
)
BUILDS_INPROGRESS = Gauge("binderhub_inprogress_builds", "Builds currently in progress")
LAUNCHES_INPROGRESS = Gauge(
    "binderhub_inprogress_launches", "Launches currently in progress"
)


def _get_image_basename_and_tag(full_name):
    """Get a supposed image name and tag without the registry part
    :param full_name: full image specification, e.g. "gitlab.com/user/project:tag"
    :return: tuple of image name and tag, e.g. ("user/project", "tag")
    """
    # the tag is either after the last (and only) colon, or not given at all,
    # in which case "latest" is implied
    tag_splits = full_name.rsplit(":", 1)
    if len(tag_splits) == 2:
        image_name = tag_splits[0]
        tag = tag_splits[1]
    else:
        image_name = full_name
        tag = "latest"

    if re.fullmatch("[a-z0-9]{4,40}/[a-z0-9._-]{2,255}", image_name):
        # if it looks like a Docker Hub image name, we're done
        return image_name, tag
    # if the image isn't implied to origin at Docker Hub,
    # the first part has to be a registry
    image_basename = "/".join(image_name.split("/")[1:])
    return image_basename, tag


def _generate_build_name(build_slug, ref, prefix="", limit=63, ref_length=6):
    """Generate a unique build name with a limited character length.

    Guaranteed (to acceptable level) to be unique for a given user, repo,
    and ref.

    We really, *really* care that we always end up with the same
    'build_name' for a particular repo + ref, but the default max
    character limit for build names is 63. To meet this constraint, we
    include a prefixed hash of the user / repo in all build names and do
    some length limiting :)

    Note that ``build`` names only need to be unique over a shorter period
    of time, while ``image`` names need to be unique for longer. Hence,
    different strategies are used.

    We also ensure that the returned value is DNS safe, by only using
    ascii lowercase + digits. everything else is escaped
    """
    # escape parts that came from providers (build slug, ref)
    # build names are case-insensitive `.lower()` is called at the end
    build_slug = _safe_build_slug(
        build_slug, limit=limit - len(prefix) - ref_length - 1
    )
    ref = _safe_build_slug(ref, limit=ref_length, hash_length=2)

    return "{prefix}{safe_slug}-{ref}".format(
        prefix=prefix,
        safe_slug=build_slug,
        ref=ref[:ref_length],
    ).lower()


def _safe_build_slug(build_slug, limit, hash_length=6):
    """Create a unique-ish name from a slug.

    This function catches a bug where a build slug may not produce a valid
    image name (e.g. arepo name ending with _, which results in image name
    ending with '-' which is invalid). This ensures that the image name is
    always safe, regardless of build slugs returned by providers
    (rather than requiring all providers to return image-safe build slugs
    below a certain length).

    Since this changes the image name generation scheme, all existing cached
    images will be invalidated.
    """
    build_slug_hash = hashlib.sha256(build_slug.encode("utf-8")).hexdigest()
    safe_chars = set(string.ascii_letters + string.digits)

    def escape(s):
        return escapism.escape(s, safe=safe_chars, escape_char="-")

    build_slug = escape(build_slug)
    return "{name}-{hash}".format(
        name=build_slug[: limit - hash_length - 1],
        hash=build_slug_hash[:hash_length],
    ).lower()


class BuildHandler(BaseHandler):
    """A handler for working with GitHub."""

    # emit keepalives every 25 seconds to avoid idle connections being closed
    KEEPALIVE_INTERVAL = 25
    build = None

    async def emit(self, data):
        """Emit an eventstream event"""
        if type(data) is not str:
            serialized_data = json.dumps(data)
        else:
            serialized_data = data
        try:
            self.write(f"data: {serialized_data}\n\n")
            await self.flush()
        except StreamClosedError:
            app_log.warning("Stream closed while handling %s", self.request.uri)
            # raise Finish to halt the handler
            raise Finish()

    def on_finish(self):
        """Stop keepalive when finish has been called"""
        self._keepalive = False
        if self.build:
            # if we have a build, tell it to stop watching
            self.build.stop()

    async def keep_alive(self):
        """Constantly emit keepalive events

        So that intermediate proxies don't terminate an idle connection
        """
        self._keepalive = True
        while True:
            await gen.sleep(self.KEEPALIVE_INTERVAL)
            if not self._keepalive:
                return
            try:
                # lines that start with : are comments
                # and should be ignored by event consumers
                self.write(":keepalive\n\n")
                await self.flush()
            except StreamClosedError:
                return

    def send_error(self, status_code, **kwargs):
        """event stream cannot set an error code, so send an error event"""
        exc_info = kwargs.get("exc_info")
        message = ""
        if exc_info:
            message = self.extract_message(exc_info)
        if not message:
            message = responses.get(status_code, "Unknown HTTP Error")

        # this cannot be async
        evt = json.dumps(
            {
                "phase": "failed",
                "status_code": status_code,
                "message": message + "\n",
            }
        )
        self.write(f"data: {evt}\n\n")
        self.finish()

    def initialize(self):
        super().initialize()
        if self.settings["use_registry"]:
            self.registry = self.settings["registry"]

        self.event_log = self.settings["event_log"]

    async def fail(self, message):
        await self.emit(
            {
                "phase": "failed",
                "message": message + "\n",
            }
        )

    def set_default_headers(self):
        super().set_default_headers()
        # set up for sending event streams
        self.set_header("content-type", "text/event-stream")
        self.set_header("cache-control", "no-cache")

    @authenticated
    async def get(self, provider_prefix, _unescaped_spec):
        """Get a built image for a given spec and repo provider.

        Different repo providers will require different spec information. This
        function relies on the functionality of the tornado `GET` request.

        Parameters
        ----------
            provider_prefix : str
                the nickname for a repo provider (i.e. 'gh')
            spec:
                specifies information needed by the repo provider (i.e. user,
                repo, ref, etc.)

        """
        prefix = "/build/" + provider_prefix
        spec = self.get_spec_from_request(prefix)

        # verify the build token and rate limit
        build_token = self.get_argument("build_token", None)
        self.check_build_token(build_token, f"{provider_prefix}/{spec}")
        self.check_rate_limit()

        # Verify if the provider is valid for EventSource.
        # EventSource cannot handle HTTP errors, so we must validate and send
        # error messages on the eventsource.
        if provider_prefix not in self.settings["repo_providers"]:
            await self.fail(f"No provider found for prefix {provider_prefix}")
            return

        # create a heartbeat
        IOLoop.current().spawn_callback(self.keep_alive)

        spec = spec.rstrip("/")
        key = f"{provider_prefix}:{spec}"

        # get a provider object that encapsulates the provider and the spec
        try:
            provider = self.get_provider(provider_prefix, spec=spec)
        except Exception as e:
            app_log.exception("Failed to get provider for %s", key)
            await self.fail(str(e))
            return

        if provider.is_banned():
            await self.emit(
                {
                    "phase": "failed",
                    "message": f"Sorry, {spec} has been temporarily disabled from launching. Please contact admins for more info!",
                }
            )
            return

        repo_url = self.repo_url = provider.get_repo_url()

        # labels to apply to build/launch metrics
        self.repo_metric_labels = {
            "provider": provider.name,
            "repo": repo_url,
        }

        try:
            ref = await provider.get_resolved_ref()
        except Exception as e:
            await self.fail(f"Error resolving ref for {key}: {e}")
            return

        if ref is None:
            error_message = [f"Could not resolve ref for {key}. Double check your URL."]

            if provider.name == "GitHub":
                error_message.append(
                    'GitHub recently changed default branches from "master" to "main".'
                )

                if provider.unresolved_ref == "master":
                    error_message.append('Did you mean the "main" branch?')
                elif provider.unresolved_ref == "main":
                    error_message.append('Did you mean the "master" branch?')

            else:
                error_message.append("Is your repo public?")

            await self.fail(" ".join(error_message))
            return

        self.ref_url = await provider.get_resolved_ref_url()
        resolved_spec = await provider.get_resolved_spec()

        badge_base_url = self.get_badge_base_url()
        self.binder_launch_host = badge_base_url or "{proto}://{host}{base_url}".format(
            proto=self.request.protocol,
            host=self.request.host,
            base_url=self.settings["base_url"],
        )
        # These are relative URLs so do not have a leading /
        self.binder_request = "v2/{provider}/{spec}".format(
            provider=provider_prefix,
            spec=spec,
        )
        self.binder_persistent_request = "v2/{provider}/{spec}".format(
            provider=provider_prefix,
            spec=resolved_spec,
        )

        # generate a complete build name (for GitHub: `build-{user}-{repo}-{ref}`)

        image_prefix = self.settings["image_prefix"]

        # Enforces max 255 characters before image
        safe_build_slug = _safe_build_slug(
            provider.get_build_slug(), limit=255 - len(image_prefix)
        )

        build_name = _generate_build_name(
            provider.get_build_slug(), ref, prefix="build-"
        )

        image_name = self.image_name = (
            "{prefix}{build_slug}:{ref}".format(
                prefix=image_prefix, build_slug=safe_build_slug, ref=ref
            )
            .replace("_", "-")
            .lower()
        )

        if self.settings["use_registry"]:
            for _ in range(3):
                try:
                    image_manifest = await self.registry.get_image_manifest(
                        *_get_image_basename_and_tag(image_name)
                    )
                    image_found = bool(image_manifest)
                    break
                except HTTPClientError:
                    app_log.exception(
                        "Tornado HTTP Timeout error: Failed to get image manifest for %s",
                        image_name,
                    )
                    image_found = False
        else:
            # Check if the image exists locally!
            # Assume we're running in single-node mode or all binder pods are assigned to the same node!
            docker_client = docker.from_env(version="auto")
            try:
                docker_client.images.get(image_name)
            except docker.errors.ImageNotFound:
                # image doesn't exist, so do a build!
                image_found = False
            else:
                image_found = True

        if image_found:
            await self.emit(
                {
                    "phase": "built",
                    "imageName": image_name,
                    "message": "Found built image, launching...\n",
                }
            )
            with LAUNCHES_INPROGRESS.track_inprogress():
                await self.launch(provider)
            self.event_log.emit(
                "binderhub.jupyter.org/launch",
                5,
                {
                    "provider": provider.name,
                    "spec": spec,
                    "ref": ref,
                    "status": "success",
                    "build_token": self._have_build_token,
                    "origin": self.settings["normalized_origin"]
                    if self.settings["normalized_origin"]
                    else self.request.host,
                },
            )
            return

        # Prepare to build
        q = Queue()

        if self.settings["use_registry"] or self.settings["build_docker_config"]:
            push_secret = self.settings["push_secret"]
        else:
            push_secret = None

        BuildClass = self.settings.get("build_class")

        appendix = self.settings["appendix"].format(
            binder_url=self.binder_launch_host + self.binder_request,
            persistent_binder_url=self.binder_launch_host
            + self.binder_persistent_request,
            repo_url=repo_url,
            ref_url=self.ref_url,
        )

        if issubclass(BuildClass, Build):
            # Deprecated, see docstring of the Build class for more details
            build = BuildClass(
                q=q,
                # api object can be None if we are using FakeBuild
                api=self.settings.get("kubernetes_client"),
                name=build_name,
                namespace=self.settings["build_namespace"],
                repo_url=repo_url,
                ref=ref,
                image_name=image_name,
                push_secret=push_secret,
                build_image=self.settings["build_image"],
                memory_limit=self.settings["build_memory_limit"],
                memory_request=self.settings["build_memory_request"],
                docker_host=self.settings["build_docker_host"],
                node_selector=self.settings["build_node_selector"],
                appendix=appendix,
                log_tail_lines=self.settings["log_tail_lines"],
                git_credentials=provider.git_credentials,
                sticky_builds=self.settings["sticky_builds"],
            )
        else:
            build = BuildClass(
                # Commented properties should be set in traitlets config
                parent=self.settings["traitlets_parent"],
                q=q,
                name=build_name,
                # namespace=self.settings["build_namespace"],
                repo_url=repo_url,
                ref=ref,
                image_name=image_name,
                # push_secret=push_secret,
                # build_image=self.settings["build_image"],
                # memory_limit=self.settings["build_memory_limit"],
                # memory_request=self.settings["build_memory_request"],
                # docker_host=self.settings["build_docker_host"],
                # node_selector=self.settings["build_node_selector"],
                # appendix=appendix,
                # log_tail_lines=self.settings["log_tail_lines"],
                git_credentials=provider.git_credentials,
                # sticky_builds=self.settings["sticky_builds"],
            )
        self.build = build

        with BUILDS_INPROGRESS.track_inprogress():
            done = False
            failed = False

            def _check_result(future):
                nonlocal done
                nonlocal failed
                try:
                    r = future.result()
                    app_log.debug("task completed: %s", r)
                except Exception:
                    app_log.error("task failed", exc_info=True)
                    done = True
                    failed = True
                    # TODO: Propagate error to front-end

            build_starttime = time.perf_counter()
            pool = self.settings["build_pool"]
            # Start building
            submit_future = pool.submit(build.submit)
            submit_future.add_done_callback(_check_result)
            IOLoop.current().add_callback(lambda: submit_future)

            log_future = None

            # initial waiting event
            await self.emit(
                {
                    "phase": "waiting",
                    "message": "Waiting for build to start...\n",
                }
            )

            while not done:
                progress = await q.get()

                # FIXME: If pod goes into an unrecoverable stage, such as ImagePullBackoff or
                # whatever, we should fail properly.
                if progress.kind == ProgressEvent.Kind.BUILD_STATUS_CHANGE:
                    if progress.payload == ProgressEvent.BuildStatus.PENDING:
                        # nothing to do, just waiting
                        continue
                    elif progress.payload == ProgressEvent.BuildStatus.COMPLETED:
                        event = {
                            "phase": "built",
                            "message": "Built image, launching...\n",
                            "imageName": image_name,
                        }
                        done = True
                    elif progress.payload == ProgressEvent.BuildStatus.RUNNING:
                        # start capturing build logs once the pod is running
                        if log_future is None:
                            log_future = pool.submit(build.stream_logs)
                            log_future.add_done_callback(_check_result)
                        continue
                    elif progress.payload == ProgressEvent.BuildStatus.COMPLETED:
                        # Do nothing, is ok!
                        continue
                    elif progress.payload == ProgressEvent.BuildStatus.FAILED:
                        event = {"phase": "failure"}
                    elif progress.payload == ProgressEvent.BuildStatus.UNKNOWN:
                        event = {"phase": "unknown"}
                elif progress.kind == ProgressEvent.Kind.LOG_MESSAGE:
                    # The logs are coming out of repo2docker, so we expect
                    # them to be JSON structured anyway
                    event = progress.payload
                    payload = json.loads(event)
                    if payload.get("phase") in ("failure", "failed"):
                        failed = True
                        BUILD_TIME.labels(status="failure").observe(
                            time.perf_counter() - build_starttime
                        )
                        BUILD_COUNT.labels(
                            status="failure", **self.repo_metric_labels
                        ).inc()

                await self.emit(event)

        # Launch after building an image
        if not failed:
            BUILD_TIME.labels(status="success").observe(
                time.perf_counter() - build_starttime
            )
            BUILD_COUNT.labels(status="success", **self.repo_metric_labels).inc()
            with LAUNCHES_INPROGRESS.track_inprogress():
                await self.launch(provider)
            self.event_log.emit(
                "binderhub.jupyter.org/launch",
                5,
                {
                    "provider": provider.name,
                    "spec": spec,
                    "ref": ref,
                    "status": "success",
                    "build_token": self._have_build_token,
                    "origin": self.settings["normalized_origin"]
                    if self.settings["normalized_origin"]
                    else self.request.host,
                },
            )

        # Don't close the eventstream immediately.
        # (javascript) eventstream clients reconnect automatically on dropped connections,
        # so if the server closes the connection first,
        # the client will reconnect which starts a new build.
        # If we sleep here, that makes it more likely that a well-behaved
        # client will close its connection first.
        # The duration of this shouldn't matter because
        # well-behaved clients will close connections after they receive the launch event.
        await gen.sleep(60)

    async def launch(self, provider):
        """Ask JupyterHub to launch the image."""
        # Load the spec-specific configuration if it has been overridden
        repo_config = provider.repo_config(self.settings)

        # the image name (without tag) is unique per repo
        # use this to count the number of pods running with a given repo
        # if we added annotations/labels with the repo name via KubeSpawner
        # we could do this better
        image_no_tag = self.image_name.rsplit(":", 1)[0]

        # TODO: put busy users in a queue rather than fail?
        # That would be hard to do without in-memory state.
        repo_quota = repo_config.get("quota")
        pod_quota = self.settings["pod_quota"]
        if pod_quota is not None or repo_quota:
            # Fetch info on currently running users *only* if quotas are set
            matching_pods = 0

            # TODO: run a watch to keep this up to date in the background
            f = self.settings["executor"].submit(
                self.settings["kubernetes_client"].list_namespaced_pod,
                self.settings["build_namespace"],
                label_selector="app=jupyterhub,component=singleuser-server",
                _request_timeout=KUBE_REQUEST_TIMEOUT,
                _preload_content=False,
            )
            resp = await asyncio.wrap_future(f)
            pods = json.loads(resp.read())["items"]
            total_pods = len(pods)

            if pod_quota is not None and total_pods >= pod_quota:
                # check overall quota first
                LAUNCH_COUNT.labels(
                    status="pod_quota",
                    **self.repo_metric_labels,
                ).inc()
                app_log.error(f"BinderHub is full: {total_pods}/{pod_quota}")
                await self.fail("Too many users on this BinderHub! Try again soon.")
                return

            for pod in pods:
                for container in pod["spec"]["containers"]:
                    # is the container running the same image as us?
                    # if so, count one for the current repo.
                    image = container["image"].rsplit(":", 1)[0]
                    if image == image_no_tag:
                        matching_pods += 1
                        break

            if repo_quota and matching_pods >= repo_quota:
                LAUNCH_COUNT.labels(
                    status="repo_quota",
                    **self.repo_metric_labels,
                ).inc()
                app_log.error(
                    f"{self.repo_url} has exceeded quota: {matching_pods}/{repo_quota} ({total_pods} total)"
                )
                await self.fail(
                    f"Too many users running {self.repo_url}! Try again soon."
                )
                return

            if matching_pods >= 0.5 * repo_quota:
                log = app_log.warning
            else:
                log = app_log.info
            log(
                "Launching pod for %s: %s other pods running this repo (%s total)",
                self.repo_url,
                matching_pods,
                total_pods,
            )

        await self.emit(
            {
                "phase": "launching",
                "message": "Launching server...\n",
            }
        )

        launcher = self.settings["launcher"]
        retry_delay = launcher.retry_delay
        for i in range(launcher.retries):
            launch_starttime = time.perf_counter()
            if self.settings["auth_enabled"]:
                # get logged in user's name
                user_model = self.hub_auth.get_user(self)
                username = user_model["name"]
                if launcher.allow_named_servers:
                    # user can launch multiple servers, so create a unique server name
                    server_name = launcher.unique_name_from_repo(self.repo_url)
                else:
                    server_name = ""
            else:
                # create a name for temporary user
                username = launcher.unique_name_from_repo(self.repo_url)
                server_name = ""
            try:

                async def handle_progress_event(event):
                    message = event["message"]
                    await self.emit(
                        {
                            "phase": "launching",
                            "message": message + "\n",
                        }
                    )

                extra_args = {
                    "binder_ref_url": self.ref_url,
                    "binder_launch_host": self.binder_launch_host,
                    "binder_request": self.binder_request,
                    "binder_persistent_request": self.binder_persistent_request,
                }
                server_info = await launcher.launch(
                    image=self.image_name,
                    username=username,
                    server_name=server_name,
                    repo_url=self.repo_url,
                    extra_args=extra_args,
                    event_callback=handle_progress_event,
                )
            except Exception as e:
                duration = time.perf_counter() - launch_starttime
                if i + 1 == launcher.retries:
                    status = "failure"
                else:
                    status = "retry"
                # don't count retries in failure/retry
                # retry count is only interesting in success
                LAUNCH_TIME.labels(
                    status=status,
                    retries=-1,
                ).observe(time.perf_counter() - launch_starttime)
                if status == "failure":
                    # don't count retries per repo
                    LAUNCH_COUNT.labels(
                        status=status,
                        **self.repo_metric_labels,
                    ).inc()

                if i + 1 == launcher.retries:
                    # last attempt failed, let it raise
                    raise

                # not the last attempt, try again
                app_log.error(
                    "Retrying launch of %s after error (duration=%.0fs, attempt=%s): %r",
                    self.repo_url,
                    duration,
                    i + 1,
                    e,
                )
                await self.emit(
                    {
                        "phase": "launching",
                        "message": f"Launch attempt {i + 1} failed, retrying...\n",
                    }
                )
                await gen.sleep(retry_delay)
                # exponential backoff for consecutive failures
                retry_delay *= 2
                continue
            else:
                # success
                duration = time.perf_counter() - launch_starttime
                LAUNCH_TIME.labels(status="success", retries=i).observe(duration)
                LAUNCH_COUNT.labels(
                    status="success",
                    **self.repo_metric_labels,
                ).inc()
                app_log.info("Launched %s in %.0fs", self.repo_url, duration)
                break
        event = {
            "phase": "ready",
            "message": f"server running at {server_info['url']}\n",
        }
        event.update(server_info)
        await self.emit(event)

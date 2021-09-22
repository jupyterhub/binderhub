"""
Helpers for creating BinderSpawners

FIXME:
This file is defined in helm-chart/binderhub/values.yaml and is copied to
binderhub/binderspawner_mixin.py by setup.py so that it can be used by other JupyterHub
container spawners.

The BinderHub repo is just used as the distribution mechanism for this spawner, BinderHub
itself doesn't require this code.

Longer term options include:
- Move BinderSpawnerMixin to a separate Python package and include it in the Z2JH Hub
  image
- Override the Z2JH hub with a custom image built in this repository
- Duplicate the code here and in binderhub/binderspawner_mixin.py
"""
from tornado import web
from traitlets.config import Configurable
from traitlets import Bool, Unicode


class BinderSpawnerMixin(Configurable):
    """
    Mixin to convert a JupyterHub container spawner to a BinderHub spawner

    Container spawner must support the following properties that will be set
    via spawn options:
    - image: Container image to launch
    - token: JupyterHub API token
    """

    def __init__(self, *args, **kwargs):
        # Is this right? Is it possible to having multiple inheritance with both
        # classes using traitlets?
        # https://stackoverflow.com/questions/9575409/calling-parent-class-init-with-multiple-inheritance-whats-the-right-way
        # https://github.com/ipython/traitlets/pull/175
        super(BinderSpawnerMixin, self).__init__(*args, **kwargs)

    auth_enabled = Bool(
        False,
        help="""
        Enable authenticated binderhub setup.

        Requires `jupyterhub-singleuser` to be available inside the repositories
        being built.
        """,
        config=True
    )

    cors_allow_origin = Unicode(
        "",
        help="""
        Origins that can access the spawned notebooks.

        Sets the Access-Control-Allow-Origin header in the spawned
        notebooks. Set to '*' to allow any origin to access spawned
        notebook servers.

        See also BinderHub.cors_allow_origin in binderhub config
        for controlling CORS policy for the BinderHub API endpoint.
        """,
        config=True
    )

    def get_args(self):
        if self.auth_enabled:
            args = super().get_args()
        else:
            args = [
                '--ip=0.0.0.0',
                f'--port={self.port}',
                f'--NotebookApp.base_url={self.server.base_url}',
                f"--NotebookApp.token={self.user_options['token']}",
                '--NotebookApp.trust_xheaders=True',
            ]
            if self.default_url:
                args.append(f'--NotebookApp.default_url={self.default_url}')

            if self.cors_allow_origin:
                args.append('--NotebookApp.allow_origin=' + self.cors_allow_origin)
            # allow_origin=* doesn't properly allow cross-origin requests to single files
            # see https://github.com/jupyter/notebook/pull/5898
            if self.cors_allow_origin == '*':
                args.append('--NotebookApp.allow_origin_pat=.*')
            args += self.args
        return args

    def start(self):
        if not self.auth_enabled:
            if 'token' not in self.user_options:
                raise web.HTTPError(400, "token required")
            if 'image' not in self.user_options:
                raise web.HTTPError(400, "image required")
        if 'image' in self.user_options:
            self.image = self.user_options['image']
        return super().start()

    def get_env(self):
        env = super().get_env()
        if 'repo_url' in self.user_options:
            env['BINDER_REPO_URL'] = self.user_options['repo_url']
        for key in (
                'binder_ref_url',
                'binder_launch_host',
                'binder_persistent_request',
                'binder_request'):
            if key in self.user_options:
                env[key.upper()] = self.user_options[key]
        return env

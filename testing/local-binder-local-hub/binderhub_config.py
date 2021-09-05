######################################################################
## A development config to test BinderHub locally.
#
# Run `python3 -m binderhub -f binderhub_config.py` in one terminal
# Run `jupyterhub --config=binderhub_config.py` in another terminal

# Host IP is needed in a few places
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
hostip = s.getsockname()[0]
s.close()


######################################################################
## BinderHub config

from binderhub.build_local import LocalRepo2dockerBuild


c.BinderHub.debug = True
c.BinderHub.use_registry = False
c.BinderHub.builder_required = False

c.BinderHub.build_class = LocalRepo2dockerBuild
c.BinderHub.push_secret = None

c.BinderHub.about_message = "<blink>Hello world.</blink>"
c.BinderHub.banner_message = 'This is headline <a href="#">news.</a>'

c.BinderHub.hub_url = f'http://{hostip}:8000'

# Shared with JupyterHub
api_token = "secretsecretsecretsecretsecretsecret"
c.BinderHub.hub_api_token = api_token



######################################################################
## JupyterHub config
from tornado import web

cors = {}
auth_enabled = False

from dockerspawner import DockerSpawner

# image & token are set via spawn options
class LocalContainerSpawner(DockerSpawner):
    # Copied from
    # https://github.com/jupyterhub/binderhub/blob/be94c46009c970617be45e27c9a6ed95203b4af0/helm-chart/binderhub/values.yaml#L82-L124
    def get_args(self):
        if auth_enabled:
            args = super().get_args()
        else:
            args = [
                '--ip=0.0.0.0',
                '--port=%i' % self.port,
                '--NotebookApp.base_url=%s' % self.server.base_url,
                '--NotebookApp.token=%s' % self.user_options['token'],
                '--NotebookApp.trust_xheaders=True',
            ]
            allow_origin = cors.get('allowOrigin')
            if allow_origin:
                args.append('--NotebookApp.allow_origin=' + allow_origin)
            # allow_origin=* doesn't properly allow cross-origin requests to single files
            # see https://github.com/jupyter/notebook/pull/5898
            if allow_origin == '*':
                args.append('--NotebookApp.allow_origin_pat=.*')
            args += self.args
        return args

    def start(self):
        if not auth_enabled:
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

c.JupyterHub.spawner_class = LocalContainerSpawner
c.DockerSpawner.remove = True
c.LocalContainerSpawner.cmd = 'jupyter-notebook'

c.Application.log_level = 'DEBUG'
c.JupyterHub.Spawner.debug = True
c.JupyterHub.authenticator_class = "nullauthenticator.NullAuthenticator"

c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_connect_ip = hostip

c.JupyterHub.services = [{
    "name": "binder",
    "admin": True,
    "api_token": api_token,
}]

# A development config to test BinderHub's UI. The image building or the
# subsequent launching of the built image in a JupyterHub is mocked so that
# users get stuck forever waiting for a build to complete.

# Deployment assumptions:
# - BinderHub:  standalone local installation
# - JupyterHub: mocked

from binderhub.build import FakeBuild
from binderhub.registry import FakeRegistry
from binderhub.repoproviders import FakeProvider

c.BinderHub.debug = True
c.BinderHub.use_registry = True
c.BinderHub.registry_class = FakeRegistry
c.BinderHub.builder_required = False
c.BinderHub.repo_providers = {"fake": FakeProvider}
c.BinderHub.build_class = FakeBuild

# Uncomment the following line to enable BinderHub's API only mode
# With this, we can then use the `build_only` query parameter in the request
# to not launch the image after build
# c.BinderHub.enable_api_only_mode = True

c.BinderHub.about_message = "<blink>Hello world.</blink>"
c.BinderHub.banner_message = 'This is headline <a href="#">news.</a>'

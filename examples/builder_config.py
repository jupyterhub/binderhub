# Configuration file for builderhub (configuration defaults example).


## Full path of config file. If relative path is provided it is taken relative to current directory.
#c.builder.config_file='builder_config.py'

## Port for builder to listen on.
#c.builder.port = 8585

## Kubernetes secret object that provides credentials for pushing built images.
#c.builder.docker-push-secret = ''

## Prefix for all built docker images.
#c.builder.docker_image_prefix = ''

# TODO: Factor this out!
#c.builder.github_auth_token = ''

## Turn on debugging if True.
#c.builder.debug = True

## Template used to generate the URL to redirect user after building image.
# Example: 'mydomain.org/hub/tmplogin?image={image}'
#c.builder.hub_redirect_url_template = ''

## Kubernetes namespace to spawn build pods in.
#c.builder.build_namespace = ''

## s2i builder image to use for doing builds.
#c.builder.build_image_spec = ''

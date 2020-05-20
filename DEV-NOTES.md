# DONE
- tini for binder deployment, it is not shutting down.
- hub_url_local introduced to solve this issue:
  hub_url is used in the Launcher(), and then it needs to be the public url
  accessible by the browser, but also in a health check, and then it needs to be
  a local url accessible by the binderhub. In my case now, there is a port
  mismatch while developing locally, and no matter, it will be a waste to make a
  "hairpin" request that goes to internet and back if there is a local path to
  the hub.
- autohttps need to avoid a failing state with pebble/letsencrypt and recover better
  DONE: https://github.com/jupyterhub/zero-to-jupyterhub-k8s/pull/1678
- Ignore warnings about HTTPS
- Ignore warnings about custom pytest marks

# TODO
- /about as liveness probe is spamming logs
- DX docs: stream closed etc issues with Chrome, but not with firefox
- Ensure BINDER_URL and HUB_URL is described in contributing sections.
- 
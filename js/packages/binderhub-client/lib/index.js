import { NativeEventSource, EventSourcePolyfill } from "event-source-polyfill";
import { EventIterator } from "event-iterator";

// Use native browser EventSource if available, and use the polyfill if not available
const EventSource = NativeEventSource || EventSourcePolyfill;

/**
 * Build (and optionally launch) a repository by talking to a BinderHub API endpoint
 */
export class BinderRepository {
  /**
   *
   * @param {string} providerSpec Spec of the form <provider>/<repo>/<ref> to pass to the binderhub API.
   * @param {URL} buildEndpointUrl API URL of the build endpoint to talk to
   * @param {string} buildToken Optional JWT based build token if this binderhub installation requires using build tokens
   * @param {boolean} buildOnly Opt out of launching built image by default by passing `build_only` param
   */
  constructor(providerSpec, buildEndpointUrl, buildToken, buildOnly) {
    this.providerSpec = providerSpec;
    // Make sure that buildEndpointUrl is a real URL - this ensures hostname is properly set
    if (!(buildEndpointUrl instanceof URL)) {
      throw new TypeError(
        `buildEndpointUrl must be a URL object, got ${buildEndpointUrl} instead`,
      );
    }
    // We make a copy here so we don't modify the passed in URL object
    this.buildEndpointUrl = new URL(buildEndpointUrl);
    // The binderHub API is path based, so the buildEndpointUrl must have a trailing slash. We add
    // it if it is not passed in here to us.
    if (!this.buildEndpointUrl.pathname.endsWith("/")) {
      this.buildEndpointUrl.pathname += "/";
    }

    // The actual URL we'll make a request to build this particular providerSpec
    this.buildUrl = new URL(this.providerSpec, this.buildEndpointUrl);
    if (buildToken) {
      this.buildUrl.searchParams.append("build_token", buildToken);
    }

    if (buildOnly) {
      this.buildUrl.searchParams.append("build_only", "true");
    }

    this.eventIteratorQueue = null;
  }

  /**
   * Call the binderhub API and yield responses as they come in
   *
   * Returns an Async Generator yielding each item returned by the
   * server API.
   *
   * @typedef Line
   * @prop {[string]} phase The phase the build is currently in. One of: building, built, fetching, launching, ready, unknown, waiting
   * @prop {[string]} message Human readable message to display to the user. Extra newlines must *not* be added
   * @prop {[string]} imageName (only with built) Full name of the image that has been built
   * @prop {[string]} binder_launch_host (only with phase=ready) The host this binderhub API request was serviced by.
   *                                     Could be different than the host the request was made to in federated cases
   * @prop {[string]} binder_request (only with phase=ready) Request used to construct this image, of form v2/<provider>/<repo>/<ref>
   * @prop {[string]} binder_persistent_request (only with phase=ready) Same as binder_request, but <ref> is fully resolved
   * @prop {[string]} binder_ref_url (only with phase=ready) A URL to the repo provider where the repo can be browsed
   * @prop {[string]} image (only with phase=ready) Full name of the image that has been built
   * @prop {[string]} token (only with phase=ready) Token to use to authenticate with jupyter server at url
   * @prop {[string]} url (only with phase=ready) URL where a jupyter server has been started
   * @prop {[string]} repo_url (only with phase=ready) URL of the repository that is ready to be launched
   *
   * @returns {AsyncGenerator<Line>} An async generator yielding responses from the API as they come in
   */
  fetch() {
    this.eventSource = new EventSource(this.buildUrl);
    return new EventIterator((queue) => {
      this.eventIteratorQueue = queue;
      this.eventSource.onerror = (err) => {
        queue.push({
          phase: "failed",
          message: "Failed to connect to event stream\n",
        });
        queue.stop();
      };

      this.eventSource.addEventListener("message", (event) => {
        // console.log("message received")
        // console.log(event)
        const data = JSON.parse(event.data);
        // FIXME: fix case of phase/state upstream
        if (data.phase) {
          data.phase = data.phase.toLowerCase();
        }
        queue.push(data);
      });
    });
  }

  /**
   * Close the EventSource connection to the BinderHub API if it is open
   */
  close() {
    if (this.eventSource !== undefined) {
      this.eventSource.close();
    }
    if (this.eventIteratorQueue !== null) {
      // Stop any currently running fetch() iterations
      this.eventIteratorQueue.stop();
    }
  }

  /**
   * Get URL to redirect user to on a Jupyter Server to display a given path

   * @param {URL} serverUrl URL to the running jupyter server
   * @param {string} token Secret token used to authenticate to the jupyter server
   * @param {string} path The path of the file or url suffix to launch the user into
   * @param {string} pathType One of "lab", "file" or "url", denoting what kinda path we are launching the user into
   *
   * @returns {URL} A URL to redirect the user to
   */
  getFullRedirectURL(serverUrl, token, path, pathType) {
    // Make a copy of the URL so we don't mangle the original
    let url = new URL(serverUrl);
    if (path) {
      // strip trailing / from URL
      url.pathname = url.pathname.replace(/\/$/, "");

      // trim leading '/' from path to launch users into
      path = path.replace(/(^\/)/g, "");

      if (pathType === "lab") {
        // The path is a specific *file* we should open with JupyterLab

        // trim trailing / on file paths
        path = path.replace(/(\/$)/g, "");

        // /doc/tree is safe because it allows redirect to files
        url.pathname = url.pathname + "/doc/tree/" + encodeURI(path);
      } else if (pathType === "file") {
        // The path is a specific file we should open with *classic notebook*

        // trim trailing / on file paths
        path = path.replace(/(\/$)/g, "");
        // /tree is safe because it allows redirect to files
        url.pathname = url.pathname + "/tree/" + encodeURI(path);
      } else {
        // pathType is 'url' and we should just pass it on
        url.pathname = url.pathname + "/" + path;
      }
    }

    url.searchParams.append("token", token);
    return url;
  }
}

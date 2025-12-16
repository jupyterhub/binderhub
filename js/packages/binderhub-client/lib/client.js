import { EventSource } from "eventsource";
import { EventIterator } from "event-iterator";

function _getXSRFToken() {
  // from @jupyterlab/services
  // https://github.com/jupyterlab/jupyterlab/blob/69223102d717f3d3e9f976d32e657a4e2456e85d/packages/services/src/contents/index.ts#L1178-L1184
  let cookie = "";
  try {
    cookie = document.cookie;
  } catch (e) {
    // e.g. SecurityError in case of CSP Sandbox
    return null;
  }
  // extracts the value of the cookie named `_xsrf`
  // by picking up everything between `_xsrf=` and the next semicolon or end-of-line
  // `\b` ensures word boundaries, so it doesn't pick up `something_xsrf=`...
  const xsrfTokenMatch = cookie.match("\\b_xsrf=([^;]*)\\b");
  if (xsrfTokenMatch) {
    return xsrfTokenMatch[1];
  }
  return null;
}

/* throw this to close the event stream */
class EventStreamRetry extends Error {}

/**
 * Build (and optionally launch) a repository by talking to a BinderHub API endpoint
 */
export class BinderRepository {
  /**
   *
   * @param {string} providerSpec Spec of the form <provider>/<repo>/<ref> to pass to the binderhub API.
   * @param {URL} buildEndpointUrl API URL of the build endpoint to talk to
   * @param {Object} [options] - optional arguments
   * @param {string} [options.buildToken] Optional JWT based build token if this binderhub installation requires using build tokens
   * @param {boolean} [options.buildOnly] Opt out of launching built image by default by passing `build_only` param
   * @param {string} [options.apiToken] Optional Bearer token for authenticating requests
   */
  constructor(providerSpec, buildEndpointUrl, options) {
    const { apiToken, buildToken, buildOnly } = options || {};

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
    this.apiToken = apiToken;

    this.stopQueue = null;
  }

  /**
   * Call the binderhub API and yield responses as they come in
   *
   * Returns an Async iterator yielding each item returned by the
   * server API.
   *
   * @typedef Line
   * @prop {string} [phase] The phase the build is currently in. One of: building, built, fetching, launching, ready, unknown, waiting
   * @prop {string} [message] Human readable message to display to the user. Extra newlines must *not* be added
   * @prop {string} [imageName] (only with built) Full name of the image that has been built
   * @prop {string} [binder_launch_host] (only with phase=ready) The host this binderhub API request was serviced by.
   *                                     Could be different than the host the request was made to in federated cases
   * @prop {string} [binder_request] (only with phase=ready) Request used to construct this image, of form v2/<provider>/<repo>/<ref>
   * @prop {string} [binder_persistent_request] (only with phase=ready) Same as binder_request, but <ref> is fully resolved
   * @prop {string} [binder_ref_url] (only with phase=ready) A URL to the repo provider where the repo can be browsed
   * @prop {string} [image] (only with phase=ready) Full name of the image that has been built
   * @prop {string} [token] (only with phase=ready) Token to use to authenticate with jupyter server at url
   * @prop {string} [url] (only with phase=ready) URL where a jupyter server has been started
   * @prop {string} [repo_url] (only with phase=ready) URL of the repository that is ready to be launched
   *
   * @returns {AsyncIterable<Line>} An async iterator yielding responses from the API as they come in
   */
  fetch() {
    const headers = {};

    if (this.apiToken && this.apiToken.length > 0) {
      headers["Authorization"] = `Bearer ${this.apiToken}`;
    } else {
      const xsrf = _getXSRFToken();
      if (xsrf) {
        headers["X-Xsrftoken"] = xsrf;
      }
    }

    const es = new EventSource(this.buildUrl, {
      fetch: async (input, init) => {
        const response = await fetch(input, {
          ...init,
          headers: { ...init.headers, ...headers },
        });
        // Known failures are passed on and handled in onError
        if (response.ok) {
          return response;
        } else if (
          response.status >= 400 &&
          response.status < 500 &&
          response.status !== 429
        ) {
          return response;
        }
        // Otherwise, throw, triggering a retry
        throw new EventStreamRetry();
      },
    });

    return new EventIterator((queue) => {
      this.stopQueue = () => queue.stop();

      const onMessage = (event) => {
        if (!event.data || event.data === "") {
          // onmessage is called for the empty lines
          return;
        }
        const data = JSON.parse(event.data);
        // FIXME: fix case of phase/state upstream
        if (data.phase) {
          data.phase = data.phase.toLowerCase();
        }
        queue.push(data);
        if (data.phase === "failed") {
          queue.stop();
        }
      };

      const onError = (error) => {
        queue.push({
          phase: "unknown",
          message: `Error in event stream: ${error}\n`,
        });
        queue.stop();
      };

      es.addEventListener("message", onMessage);
      es.addEventListener("error", onError);
      return () => {
        es.removeEventListener("message", onMessage);
        es.removeEventListener("error", onError);
        es.close();
      };
    });
  }

  /**
   * Close the EventSource connection to the BinderHub API if it is open
   */
  close() {
    if (this.stopQueue) {
      // close event source
      this.stopQueue();
      this.stopQueue = null;
    }
  }
}

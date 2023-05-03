import { NativeEventSource, EventSourcePolyfill } from 'event-source-polyfill';

// Use native browser EventSource if available, and use the polyfill if not available
const EventSource = NativeEventSource || EventSourcePolyfill;

/**
 * Build and launch a repository by talking to a BinderHub API endpoint
 */
export class BinderRepository {
  /**
   *
   * @param {string} providerSpec Spec of the form <provider>/<repo>/<ref> to pass to the binderhub API.
   * @param {string} baseUrl Base URL (including the trailing slash) of the binderhub installation to talk to.
   * @param {string} buildToken Optional JWT based build token if this binderhub installation requires using build tokesn
   */
  constructor(providerSpec, baseUrl, buildToken) {
    this.providerSpec = providerSpec;
    this.baseUrl = baseUrl;
    this.buildToken = buildToken;
    this.callbacks = {};
    this.state = null;
  }

  /**
   * Call the BinderHub API
   */
  fetch() {
    let apiUrl = this.baseUrl + "build/" + this.providerSpec;
    if (this.buildToken) {
        apiUrl = apiUrl + `?build_token=${this.buildToken}`;
    }

    this.eventSource = new EventSource(apiUrl);
    this.eventSource.onerror = (err) => {
      console.error("Failed to construct event stream", err);
      this._changeState("failed", {
        message: "Failed to connect to event stream\n"
      });
    };
    this.eventSource.addEventListener("message", (event) => {
      const data = JSON.parse(event.data);
      // FIXME: Rename 'phase' to 'state' upstream
      // FIXME: fix case of phase/state upstream
      let state = null;
      if (data.phase) {
        state = data.phase.toLowerCase();
      }
      this._changeState(state, data);
    });
  }

  /**
   * Close the EventSource connection to the BinderHub API if it is open
   */
  close() {
    if (this.eventSource !== undefined) {
      this.eventSource.close();
    }
  }

  /**
   * Redirect user to a running jupyter server with given token

   * @param {URL} url URL to the running jupyter server
   * @param {string} token Secret token used to authenticate to the jupyter server
   * @param {string} path The path of the file or url suffix to launch the user into
   * @param {string} pathType One of "lab", "file" or "url", denoting what kinda path we are launching the user into
   */
  launch(url, token, path, pathType) {
    // redirect a user to a running server with a token
    if (path) {
      // strip trailing /
      url = url.replace(/\/$/, "");
      // trim leading '/'
      path = path.replace(/(^\/)/g, "");
      if (pathType === "lab") {
        // trim trailing / on file paths
        path = path.replace(/(\/$)/g, "");
        // /doc/tree is safe because it allows redirect to files
        url = url + "/doc/tree/" + encodeURI(path);
      } else if (pathType === "file") {
        // trim trailing / on file paths
        path = path.replace(/(\/$)/g, "");
        // /tree is safe because it allows redirect to files
        url = url + "/tree/" + encodeURI(path);
      } else {
        // pathType === 'url'
        url = url + "/" + path;
      }
    }
    const sep = url.indexOf("?") == -1 ? "?" : "&";
    url = url + sep + $.param({ token: token });
    window.location.href = url;
  }


  /**
   * Add callback whenever state of the current build changes
   *
   * @param {str} state The state to add this callback to. '*' to add callback for all state changes
   * @param {*} cb Callback function to call whenever this state is reached
   */
  onStateChange(state, cb) {
    if (this.callbacks[state] === undefined) {
      this.callbacks[state] = [cb];
    } else {
      this.callbacks[state].push(cb);
    }
  }

  /**
   * @param {string} oldState Old state the building process was in
   * @param {string} newState New state the building process is in
   * @returns True if transition from oldState to newState is valid, False otherwise
   */
  validateStateTransition(oldState, newState) {
    if (oldState === "start") {
      return (
        newState === "waiting" || newState === "built" || newState === "failed"
      );
    } else if (oldState === "waiting") {
      return newState === "building" || newState === "failed";
    } else if (oldState === "building") {
      return newState === "pushing" || newState === "failed";
    } else if (oldState === "pushing") {
      return newState === "built" || newState === "failed";
    } else {
      return false;
    }
  }

  _changeState(state, data) {
    [state, "*"].map(key => {
      const callbacks = this.callbacks[key];
      if (callbacks) {
        for (let i = 0; i < callbacks.length; i++) {
          callbacks[i](this.state, state || this.state, data);
        }
      }
    });

    if (state && this.validateStateTransition(this.state, state)) {
      this.state = state;
    }
  }
}

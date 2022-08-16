import { NativeEventSource, EventSourcePolyfill } from 'event-source-polyfill';

const EventSource = NativeEventSource || EventSourcePolyfill;

export default class BinderImage {
  constructor(providerSpec, baseUrl, buildToken) {
    this.providerSpec = providerSpec;
    this.baseUrl = baseUrl;
    this.buildToken = buildToken;
    this.callbacks = {};
    this.state = null;
  }

  fetch() {
    let apiUrl = this.baseUrl + "build/" + this.providerSpec;
    if (this.buildToken) {
        apiUrl = apiUrl + `?build_token=${this.buildToken}`;
    }

    this.eventSource = new EventSource(apiUrl);
    this.eventSource.onerror = (err) => {
      console.error("Failed to construct event stream", err);
      this.changeState("failed", {
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
      this.changeState(state, data);
    });
  }

  close() {
    if (this.eventSource !== undefined) {
      this.eventSource.close();
    }
  }

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

  onStateChange(state, cb) {
    if (this.callbacks[state] === undefined) {
      this.callbacks[state] = [cb];
    } else {
      this.callbacks[state].push(cb);
    }
  }

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

  changeState(state, data) {
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

export class LaunchSpec {
  /**
   *
   * @param {string} urlPath Path inside the Jupyter server to redirect the user to after launching
   */
  constructor(urlPath) {
    this.urlPath = urlPath;
    // Ensure no leading / here
    this.urlPath = this.urlPath.replace(/^\/*/, "");
  }

  /**
   * Return a URL to redirect user to for use with this launch specification
   *
   * @param {URL} serverUrl Fully qualified URL to a running Jupyter Server
   * @param {string} token Authentication token to pass to the Jupyter Server
   *
   * @returns {URL}
   */
  getJupyterServerRedirectUrl(serverUrl, token) {
    const redirectUrl = new URL(this.urlPath, serverUrl);
    redirectUrl.searchParams.append("token", token);
    return redirectUrl;
  }

  /**
   * Create a LaunchSpec from given query parameters in the URL
   *
   * Handles backwards compatible parameters as needed.
   *
   * @param {URLSearchParams} searchParams
   *
   * @returns {LaunchSpec}
   */
  static fromSearchParams(searchParams) {
    let urlPath = searchParams.get("urlpath");
    if (urlPath === null) {
      urlPath = "";
    }

    // Handle legacy parameters for opening URLs after launching
    // labpath and filepath
    if (searchParams.has("labpath")) {
      // Trim trailing / on file paths
      const filePath = searchParams.get("labpath").replace(/(\/$)/g, "");
      urlPath = `doc/tree/${encodeURI(filePath)}`;
    } else if (searchParams.has("filepath")) {
      // Trim trailing / on file paths
      const filePath = searchParams.get("filepath").replace(/(\/$)/g, "");
      urlPath = `tree/${encodeURI(filePath)}`;
    }

    return new LaunchSpec(urlPath);
  }
}

/**
 * A full binder specification
 *
 * Includes a *build* specification (determining what is built), and a
 * *launch* specification (determining what is launched).
 */
export class Spec {
  /**
   * @param {string} buildSpec Build specification, passed directly to binderhub API
   * @param {LaunchSpec} launchSpec Launch specification, determining what is launched
   */
  constructor(buildSpec, launchSpec) {
    this.buildSpec = buildSpec;
    this.launchSpec = launchSpec;
  }
}

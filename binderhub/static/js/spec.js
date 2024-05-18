export class RuntimeParams {
  /**
   *
   * @param {string} urlPath
   */
  constructor(urlPath) {
    this.urlPath = urlPath;
    // Ensure no leading / here
    this.urlPath = this.urlPath.replace(/^\/*/, "");
  }

  /**
   *
   * @param {URLSearchParams} searchParams
   *
   * @returns {RuntimeParams}
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

    return new RuntimeParams(urlPath);
  }
}

export class Spec {
  /**
   * @param {string} buildSpec
   * @param {RuntimeParams} runtimeParams
   */
  constructor(buildSpec, runtimeParams) {
    this.buildSpec = buildSpec;
    this.runtimeParams = runtimeParams;
  }
}

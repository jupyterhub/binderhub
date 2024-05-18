/**
 * @typedef {object} NBViewerIFrameProps
 * @prop {string} spec
 * @prop {string} urlPath
 * @param {NBViewerIFrameProps} props
 * @returns
 */
export function NBViewerIFrame({ spec, urlPath }) {
  // We only support GitHub links as preview right now
  if (!spec.startsWith("gh/")) {
    return;
  }

  const [_, org, repo, ref] = spec.split("/");

  urlPath = decodeURI(urlPath);
  // Handle cases where urlPath starts with a `/`
  urlPath = urlPath.replace(/^\//, "");
  let filePath = "";
  if (urlPath.startsWith("doc/tree/")) {
    filePath = urlPath.replace(/^doc\/tree\//, "");
  } else if (urlPath.startsWith("tree/")) {
    filePath = urlPath.replace(/^tree\//, "");
  }

  let url;
  if (filePath) {
    url = `https://nbviewer.jupyter.org/github/${org}/${repo}/blob/${ref}/${filePath}`;
  } else {
    url = `https://nbviewer.jupyter.org/github/${org}/${repo}/tree/${ref}`;
  }

  return (
    <div className="row vh-100 mt-4 p-4 text-center">
      <p>
        Here is a non-interactive preview on{" "}
        <a target="_blank" href="https://nbviewer.jupyter.org">
          nbviewer
        </a>{" "}
        while we start a server for you. <br />
        Your binder will open automatically when it is ready.
      </p>
      <iframe src={url} className="h-100"></iframe>
    </div>
  );
}

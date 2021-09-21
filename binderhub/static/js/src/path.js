export function getPathType() {
  // return path type. 'file' or 'url'
  const element = document.getElementById("url-or-file-selected");
  let pathType = element.innerText.trim().toLowerCase();
  if (pathType === "file") {
    // selecting a 'file' in the form opens with jupyterlab
    // avoids backward-incompatibility with old `filepath` urls,
    // which still open old UI
    pathType = "lab";
  }
  return pathType;
}

export function updatePathText() {
  const pathType = getPathType();
  let text;
  if (pathType === "file") {
    text = "Path to a notebook file (optional)";
  } else {
    text = "URL to open (optional)";
  }
  const filePathElement = document.getElementById("filepath");
  filePathElement.setAttribute("placeholder", text);

  const filePathElementLabel = document.querySelector("label[for=filepath]");
  filePathElementLabel.innerText = text;
}

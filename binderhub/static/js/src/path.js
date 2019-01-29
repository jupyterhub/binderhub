export function getPathType() {
  // return path type. 'file' or 'url'
  const element = document.getElementById("url-or-file-selected");
  return element.innerText.trim().toLowerCase();
}

export function updatePathText() {
  var pathType = getPathType();
  var text;
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

import { useEffect, useState } from "react";
import copy from "copy-to-clipboard";

/**
 * @typedef {object} ProviderSelectorProps
 * @prop {import("../App").Provider[]} providers
 * @prop {import("../App").Provider} selectedProvider
 * @prop {(p: import("../App").Provider) => void} setSelectedProvider
 *
 * @param {ProviderSelectorProps} props
 * @returns
 */
function ProviderSelector({
  providers,
  selectedProvider,
  setSelectedProvider,
}) {
  return (
    <>
      <button
        className="btn btn-secondary border border-2 border-end-0 dropdown-toggle"
        type="button"
        data-bs-toggle="dropdown"
        aria-expanded="false"
        aria-controls="repository-type-dropdown"
        aria-label="Select repository type"
      >
        {selectedProvider.displayName}
      </button>
      <ul
        id="repository-type-dropdown"
        className="dropdown-menu dropdown-menu-start"
      >
        {providers.map((p) => (
          <li key={p.id}>
            <button
              className="dropdown-item"
              onClick={() => setSelectedProvider(p)}
              type="button"
            >
              {p.displayName}
            </button>
          </li>
        ))}
      </ul>
    </>
  );
}

function UrlSelector({ setUrlPath }) {
  const KINDS = [
    {
      id: "file",
      displayName: "File",
      placeholder: "eg. index.ipynb",
      label: "File to open (in JupyterLab)",
      // Using /doc/tree as that opens documents *and* notebook files
      getUrlPath: (input) => `/doc/tree/${input}`,
    },
    {
      id: "url",
      displayName: "URL",
      placeholder: "eg. /rstudio",
      label: "URL to open",
      getUrlPath: (input) => input,
    },
  ];

  const [kind, setKind] = useState(KINDS[0]);
  const [path, setPath] = useState("");

  useEffect(() => {
    if (path) {
      setUrlPath(kind.getUrlPath(path));
    } else {
      setUrlPath("");
    }
  }, [kind, path]);

  return (
    <>
      <label htmlFor="path" className="form-label">
        {kind.label}
      </label>
      <div className="input-group">
        <input
          className="form-control border border-2 border-end-0"
          type="text"
          id="path"
          name="path"
          placeholder={kind.placeholder}
          onChange={(e) => setPath(e.target.value)}
        />
        <button
          className="btn btn-secondary border border-2 border-start-0 dropdown-toggle"
          type="button"
          data-bs-toggle="dropdown"
          aria-expanded="false"
        >
          {kind.displayName}
        </button>
        <ul className="dropdown-menu dropdown-menu-end">
          {KINDS.map((k) => (
            <li key={k.id}>
              <button
                className="dropdown-item"
                onClick={() => setKind(k)}
                type="button"
              >
                {k.displayName}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}

/**
 *
 * @param {URL} publicBaseUrl
 * @param {import("../App").Provider} provider
 * @param {string} repo
 * @param {string} ref
 * @param {string} urlPath
 * @returns
 */
function makeShareableUrl(publicBaseUrl, provider, repo, ref, urlPath) {
  const encodedRepo = provider.repo.urlEncode ? encodeURIComponent(repo) : repo;
  const url = new URL(`v2/${provider.id}/${encodedRepo}/${ref}`, publicBaseUrl);
  if (urlPath) {
    url.searchParams.set("urlpath", urlPath);
  }
  return url;
}

export function LinkGenerator({
  providers,
  publicBaseUrl,
  selectedProvider,
  setSelectedProvider,
  repo,
  setRepo,
  reference,
  setReference,
  urlPath,
  setUrlPath,
  isLaunching,
  setIsLaunching,
  className,
}) {
  const [badgeType, setBadgeType] = useState("md"); // Options are md and rst
  const [badgeVisible, setBadgeVisible] = useState(false);

  let launchUrl = "";
  let badgeMarkup = "";

  const ref =
    reference ||
    (selectedProvider.ref.enabled ? selectedProvider.ref.default : "");
  if (repo !== "" && (!selectedProvider.ref.enabled || ref !== "")) {
    launchUrl = makeShareableUrl(
      publicBaseUrl,
      selectedProvider,
      repo,
      ref,
      urlPath,
    ).toString();
    const badgeLogoUrl = new URL("badge_logo.svg", publicBaseUrl);
    if (badgeType === "md") {
      badgeMarkup = `[![Binder](${badgeLogoUrl})](${launchUrl})`;
    } else {
      badgeMarkup = `.. image:: ${badgeLogoUrl}\n :target: ${launchUrl}`;
    }
  }

  return (
    <form className={`d-flex flex-column gap-3 ${className}`}>
      <h4>Build and launch a repository</h4>
      <fieldset>
        <legend className="form-label">{selectedProvider.repo.label}</legend>
        <div className="input-group">
          <ProviderSelector
            providers={providers}
            selectedProvider={selectedProvider}
            setSelectedProvider={setSelectedProvider}
          />
          <input
            className="form-control border border-2 border-start-0"
            type="text"
            name="repository"
            placeholder={selectedProvider.repo.placeholder}
            disabled={isLaunching}
            aria-label="Enter repository URL"
            onChange={(e) => {
              let repo = e.target.value;
              if (selectedProvider.detect && selectedProvider.detect.regex) {
                // repo value *must* be detected by this regex, or it is not valid yet
                const re = new RegExp(selectedProvider.detect.regex);
                const results = re.exec(repo);
                if (results !== null && results.groups && results.groups.repo) {
                  setRepo(results.groups.repo);
                }
              } else {
                setRepo(e.target.value);
              }
            }}
          />
        </div>
      </fieldset>

      <div className="row align-items-end">
        <div className="col-5">
          <label htmlFor="ref" className="form-label">
            Git ref (branch, tag, or commit)
          </label>
          <div className="input-group">
            <input
              className="form-control border border-2"
              type="text"
              id="ref"
              name="ref"
              disabled={!selectedProvider.ref.enabled || isLaunching}
              placeholder={
                (selectedProvider.ref.enabled &&
                  selectedProvider.ref.default) ||
                ""
              }
              onChange={(e) => {
                setReference(e.target.value);
              }}
            />
          </div>
        </div>
        <div className="col-5">
          <UrlSelector setUrlPath={setUrlPath} />
        </div>
        <div className="col-2">
          <button
            className="btn btn-primary col-2 w-100"
            disabled={isLaunching}
            onClick={() => setIsLaunching(true)}
          >
            {isLaunching ? "launching..." : "launch"}
          </button>
        </div>
      </div>

      <div>
        <div className="input-group">
          <div
            className="form-control font-monospace border border-2 border-end-0"
            data-testid="launch-url"
          >
            {launchUrl ||
              "Fill in the fields to see a URL for sharing your Binder."}
          </div>
          <button
            className="btn btn-outline-secondary border border-2 border-start-0"
            type="button"
            id="copy-url"
            onClick={() => copy(launchUrl)}
            disabled={launchUrl === ""}
          >
            <i className="bi bi-copy"></i>
          </button>
        </div>
      </div>

      <div className="card">
        <div className="card-header d-flex align-items-baseline">
          <span className="flex-fill">Badges for your README</span>
          <button
            className="btn btn-link"
            type="button"
            aria-controls="badge-container"
            aria-expanded={badgeVisible}
            onClick={() => {
              setBadgeVisible(!badgeVisible);
            }}
          >
            {badgeVisible ? "hide" : "show"}
          </button>
        </div>
        <div
          className={`card-body ${badgeVisible ? "" : "d-none"}`}
          id="badge-container"
        >
          <div className="d-flex align-items-baseline">
            <div
              className="btn-group"
              role="group"
              aria-label="Basic radio toggle button group"
            >
              <input
                type="radio"
                className="btn-check"
                name="btn-badge"
                id="btn-badge-md"
                defaultChecked={true}
                autoComplete="off"
                onClick={() => setBadgeType("md")}
              ></input>
              <label
                title="markdown"
                className="btn btn-outline-secondary font-monospace"
                htmlFor="btn-badge-md"
              >
                md
              </label>

              <input
                type="radio"
                className="btn-check"
                name="btn-badge"
                id="btn-badge-rst"
                autoComplete="off"
                onClick={() => setBadgeType("rst")}
              ></input>
              <label
                title="reStructuredText"
                className="btn btn-outline-secondary font-monospace"
                htmlFor="btn-badge-rst"
              >
                rST
              </label>
            </div>
            <pre className="flex-fill font-monospace px-1">
              {badgeMarkup ||
                "Fill in the fields to see a badge markup for your README."}
            </pre>
            <button
              className="btn btn-outline-secondary"
              type="button"
              id="copy-url"
              onClick={() => copy(badgeMarkup)}
              disabled={badgeMarkup === ""}
            >
              <i className="bi bi-copy"></i>
            </button>
          </div>
        </div>
      </div>
    </form>
  );
}

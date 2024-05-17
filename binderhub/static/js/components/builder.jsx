import { BinderRepository } from "@jupyterhub/binderhub-client";
import { useEffect, useRef, useState } from "react";
import { Terminal } from "xterm";
import { FitAddon } from "xterm-addon-fit";
import "xterm/css/xterm.css";
import { Progress, PROGRESS_STATES } from "./progress.jsx";

function redirectToRunningServer(serverUrl, token, urlPath) {
  // Make sure urlPath doesn't start with a `/`
  urlPath = urlPath.replace(/^\//, "");
  const redirectUrl = new URL(urlPath, serverUrl);
  redirectUrl.searchParams.append("token", token);
  window.location.href = redirectUrl;
}

async function buildImage(
  baseUrl,
  provider,
  repo,
  ref,
  term,
  fitAddon,
  urlPath,
  setIsLaunching,
  setProgressState,
  setEnsureLogsVisible,
) {
  const providerSpec = `${provider.id}/${repo}/${ref}`;
  const buildEndPointURL = new URL("build/", baseUrl);
  const image = new BinderRepository(providerSpec, buildEndPointURL);
  // Clear the last line written, so we start from scratch
  term.write("\x1b[2K\r");
  fitAddon.fit();
  for await (const data of image.fetch()) {
    // Write message to the log terminal if there is a message
    if (data.message !== undefined) {
      // Write out all messages to the terminal!
      term.write(data.message);
      // Resize our terminal to make sure it fits messages appropriately
      fitAddon.fit();
    } else {
      console.log(data);
    }

    switch (data.phase) {
      case "failed": {
        image.close();
        setIsLaunching(false);
        setProgressState(PROGRESS_STATES.FAILED);
        setEnsureLogsVisible(true);
        break;
      }
      case "ready": {
        // Close the EventStream when the image has been built
        image.close();
        redirectToRunningServer(data.url, data.token, urlPath);
        console.log(data);
        break;
      }
      case "building": {
        setProgressState(PROGRESS_STATES.BUILDING);
        break;
      }
      case "waiting": {
        setProgressState(PROGRESS_STATES.WAITING);
        break;
      }
      case "pushing": {
        setProgressState(PROGRESS_STATES.PUSHING);
        break;
      }
      case "built": {
        setProgressState(PROGRESS_STATES.PUSHING);
        break;
      }
      case "launching": {
        setProgressState(PROGRESS_STATES.LAUNCHING);
        break;
      }
      default: {
        console.log("Unknown phase in response from server");
        console.log(data);
        break;
      }
    }
  }
}

function ImageLogs({ setTerm, setFitAddon, logsVisible, setLogsVisible }) {
  const toggleLogsButton = useRef();
  useEffect(() => {
    async function setup() {
      const term = new Terminal({
        convertEol: true,
        disableStdin: true,
      });
      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(document.getElementById("terminal"));
      fitAddon.fit();
      setTerm(term);
      setFitAddon(fitAddon);
      term.write("Logs will appear here when image is being built");
    }
    setup();
  }, []);

  return (
    <div className="card">
      <div className="card-header d-flex align-items-baseline">
        <span className="flex-fill">Build Logs</span>
        <button
          ref={toggleLogsButton}
          class="btn btn-link"
          type="button"
          aria-controls="terminal-container"
          onClick={() => {
            setLogsVisible(!logsVisible);
          }}
        >
          {logsVisible ? "hide" : "show"}
        </button>
      </div>
      <div
        className={`card-body bg-black ${logsVisible ? "" : "d-none"}`}
        id="terminal-container"
      >
        <div id="terminal"></div>
      </div>
    </div>
  );
}
export function ImageBuilder({
  baseUrl,
  selectedProvider,
  repo,
  reference,
  urlPath,
  isLaunching,
  setIsLaunching,
}) {
  const [term, setTerm] = useState(null);
  const [fitAddon, setFitAddon] = useState(null);
  const [progressState, setProgressState] = useState(null);
  const [logsVisible, setLogsVisible] = useState(false);
  useEffect(() => {
    async function setup() {
      if (isLaunching) {
        await buildImage(
          baseUrl,
          selectedProvider,
          repo,
          reference,
          term,
          fitAddon,
          urlPath,
          setIsLaunching,
          setProgressState,
          setLogsVisible,
        );
      }
    }
    setup();
  }, [isLaunching]);
  return (
    <div className="bg-light p-4">
      <Progress state={progressState} />
      <ImageLogs
        setTerm={setTerm}
        setFitAddon={setFitAddon}
        logsVisible={logsVisible}
        setLogsVisible={setLogsVisible}
      />
    </div>
  );
}

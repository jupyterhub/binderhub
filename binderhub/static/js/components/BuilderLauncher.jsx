import { BinderRepository } from "@jupyterhub/binderhub-client";
import { useEffect, useRef, useState } from "react";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import "@xterm/xterm/css/xterm.css";
import { Progress, PROGRESS_STATES } from "./Progress.jsx";

/**
 *
 * @param {URL} baseUrl
 * @param {string?} buildToken
 * @param {Spec} spec
 * @param {Terminal} term
 * @param {Array<string>} logBuffer
 * @param {FitAddon} fitAddon
 * @param {(l: boolean) => void} setIsLaunching
 * @param {(p: PROGRESS_STATES) => void} setProgressState
 * @param {(e: boolean) => void} setEnsureLogsVisible
 */
async function buildImage(
  baseUrl,
  buildToken,
  spec,
  term,
  logBuffer,
  fitAddon,
  setIsLaunching,
  setProgressState,
  setEnsureLogsVisible,
) {
  const buildEndPointURL = new URL("build/", baseUrl);
  let options = {};
  if (buildToken) {
    options.buildToken = buildToken;
  }
  const image = new BinderRepository(spec.buildSpec, buildEndPointURL, options);
  // Clear the last line written, so we start from scratch
  term.write("\x1b[2K\r");
  logBuffer.length = 0;
  fitAddon.fit();
  for await (const data of image.fetch()) {
    // Write message to the log terminal if there is a message
    if (data.message !== undefined) {
      // Write out all messages to the terminal!
      term.write(data.message);
      // Keep a copy of the message in the logBuffer
      logBuffer.push(data.message);
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
        setProgressState(PROGRESS_STATES.SUCCESS);
        image.close();
        const serverUrl = new URL(data.url);
        window.location.href = spec.launchSpec.getJupyterServerRedirectUrl(
          serverUrl,
          data.token,
        );
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

/**
 * @typedef {object} ImageLogsProps
 * @prop {(t: Terminal) => void} setTerm
 * @prop {(f: FitAddon) => void} setFitAddon
 * @prop {boolean} logsVisible
 * @prop {Ref<Array<string>>} logBufferRef
 * @prop {(l: boolean) => void} setLogsVisible
 *
 * @param {ImageLogsProps} props
 * @returns
 */
function ImageLogs({
  setTerm,
  setFitAddon,
  logsVisible,
  setLogsVisible,
  logBufferRef,
}) {
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
          className="btn btn-link"
          type="button"
          aria-controls="terminal-container"
          onClick={() => {
            setLogsVisible(!logsVisible);
          }}
        >
          {logsVisible ? "hide" : "show"}
        </button>
        <button
          className="btn btn-link"
          type="button"
          onClick={(ev) => {
            const blob = new Blob([logBufferRef.current.join("")], {
              type: "text/plain",
            });
            // Open raw logs in a new window
            window.open(window.URL.createObjectURL(blob), "_blank");
            // Prevent the toggle action from firing
            ev.stopPropagation();
          }}
        >
          view raw
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

/**
 * @typedef {object} BuildLauncherProps
 * @prop {URL} baseUrl
 * @prop {string?} buildToken
 * @prop {Spec} spec
 * @prop {boolean} isLaunching
 * @prop {(l: boolean) => void} setIsLaunching
 * @prop {PROGRESS_STATES} progressState
 * @prop {(p: PROGRESS_STATES) => void} setProgressState
 * @prop {string?} className
 *
 * @param {BuildLauncherProps} props
 * @returns
 */
export function BuilderLauncher({
  baseUrl,
  buildToken,
  spec,
  isLaunching,
  setIsLaunching,
  progressState,
  setProgressState,
  className,
}) {
  const [term, setTerm] = useState(null);
  const [fitAddon, setFitAddon] = useState(null);
  const [logsVisible, setLogsVisible] = useState(false);
  const logBufferRef = useRef(new Array());
  useEffect(() => {
    async function setup() {
      if (isLaunching) {
        await buildImage(
          baseUrl,
          buildToken,
          spec,
          term,
          logBufferRef.current,
          fitAddon,
          setIsLaunching,
          setProgressState,
          setLogsVisible,
        );
      }
    }
    setup();
  }, [isLaunching]);
  return (
    <div className={className}>
      <Progress progressState={progressState} />
      <ImageLogs
        setTerm={setTerm}
        setFitAddon={setFitAddon}
        logsVisible={logsVisible}
        setLogsVisible={setLogsVisible}
        logBufferRef={logBufferRef}
      />
    </div>
  );
}

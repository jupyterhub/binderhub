import { useEffect, useState } from "react";
import { BuilderLauncher } from "../components/BuilderLauncher.jsx";
import { useParams } from "react-router";
import { useSearchParams } from "react-router-dom";
import { NBViewerIFrame } from "../components/NBViewerIFrame.jsx";
import { LoadingIndicator } from "../components/LoadingIndicator.jsx";
import { FaviconUpdater } from "../components/FaviconUpdater.jsx";
import { LaunchSpec, Spec } from "../spec.js";

/**
 * @typedef {object} LoadingPageProps
 * @prop {URL} baseUrl
 * @param {LoadingPageProps} props
 * @returns
 */
export function LoadingPage({ baseUrl }) {
  const [progressState, setProgressState] = useState(null);

  const params = useParams();
  const buildSpec = params["*"];

  const [searchParams, _] = useSearchParams();

  const [isLaunching, setIsLaunching] = useState(false);

  const spec = new Spec(buildSpec, LaunchSpec.fromSearchParams(searchParams));

  useEffect(() => {
    // Start launching after the DOM has fully loaded
    setTimeout(() => setIsLaunching(true), 1);
  }, []);

  return (
    <>
      <LoadingIndicator progressState={progressState} />
      <BuilderLauncher
        baseUrl={baseUrl}
        spec={spec}
        isLaunching={isLaunching}
        setIsLaunching={setIsLaunching}
        progressState={progressState}
        setProgressState={setProgressState}
      />
      <FaviconUpdater progressState={progressState} />

      <NBViewerIFrame spec={spec} />
    </>
  );
}

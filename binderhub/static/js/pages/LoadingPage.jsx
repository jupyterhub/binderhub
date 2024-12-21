import { useEffect, useState } from "react";
import { BuilderLauncher } from "../components/BuilderLauncher.jsx";
import { useParams, useSearch } from "wouter";
import { NBViewerIFrame } from "../components/NBViewerIFrame.jsx";
import { LoadingIndicator } from "../components/LoadingIndicator.jsx";
import { FaviconUpdater } from "../components/FaviconUpdater.jsx";
import { LaunchSpec, Spec } from "../spec.js";
import { ErrorPage } from "../components/ErrorPage.jsx";

/**
 * @typedef {object} LoadingPageProps
 * @prop {URL} baseUrl
 * @prop {string?} buildToken
 * @prop {import("../App.jsx").Provider} provider
 * @param {LoadingPageProps} props
 * @returns
 */
export function LoadingPage({ baseUrl, buildToken, provider }) {
  const [progressState, setProgressState] = useState(null);

  const params = useParams();
  const partialSpec = params["0"];
  const buildSpec = `${provider.id}/${partialSpec}`;

  const searchParams = new URLSearchParams(useSearch());

  const [isLaunching, setIsLaunching] = useState(false);

  const spec = new Spec(buildSpec, LaunchSpec.fromSearchParams(searchParams));
  const formatError = partialSpec.match(provider.spec.validateRegex) === null;

  useEffect(() => {
    if (!formatError) {
      // Start launching after the DOM has fully loaded
      setTimeout(() => setIsLaunching(true), 1);
    }
  }, []);

  if (formatError) {
    return (
      <ErrorPage
        title="400: Bad Request"
        errorMessage={`Spec for this provider should match ${
          provider.spec.validateRegex
        }, provided: "${buildSpec.substring(buildSpec.indexOf("/") + 1)}".`}
      />
    );
  }

  return (
    <>
      <LoadingIndicator progressState={progressState} />
      <BuilderLauncher
        className="bg-custom-dark p-4 rounded"
        baseUrl={baseUrl}
        spec={spec}
        buildToken={buildToken}
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

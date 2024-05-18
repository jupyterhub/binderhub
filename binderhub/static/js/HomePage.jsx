import { LinkGenerator } from "./components/linkbuilder.jsx";
import { ImageBuilder } from "./components/builder.jsx";
import { HowItWorks } from "./components/howitworks.jsx";
import { useEffect, useState } from "react";

export function BinderHomePage({ providers, publicBaseUrl, baseUrl }) {
  const defaultProvider = providers[0];
  const [selectedProvider, setSelectedProvider] = useState(defaultProvider);
  const [repo, setRepo] = useState("");
  const [ref, setRef] = useState("");
  const [urlPath, setUrlPath] = useState("");
  const [isLaunching, setIsLaunching] = useState(false);
  const [spec, setSpec] = useState("");
  const [progressState, setProgressState] = useState(null);

  useEffect(() => {
    setSpec(`${selectedProvider.id}/${repo}/${ref}`);
  }, [selectedProvider, repo, ref]);

  return (
    <>
      <div className="text-center">
        <h5>Turn a Git repo into a collection of interactive notebooks</h5>
        <p>
          Have a repository full of Jupyter notebooks? With Binder, open those
          notebooks in an executable environment, making your code immediately
          reproducible by anyone, anywhere.
        </p>
        <p className="fw-lighter mt-8">
          New to Binder? Get started with a{" "}
          <a
            href="https://the-turing-way.netlify.app/communication/binder/zero-to-binder.html"
            target="_blank"
          >
            Zero-to-Binder tutorial
          </a>{" "}
          in Julia, Python, or R.
        </p>
      </div>
      <LinkGenerator
        publicBaseUrl={publicBaseUrl}
        providers={providers}
        selectedProvider={selectedProvider}
        setSelectedProvider={setSelectedProvider}
        repo={repo}
        setRepo={setRepo}
        reference={ref}
        setReference={setRef}
        urlPath={urlPath}
        setUrlPath={setUrlPath}
        isLaunching={isLaunching}
        setIsLaunching={setIsLaunching}
      />
      <ImageBuilder
        baseUrl={baseUrl}
        spec={spec}
        urlPath={urlPath}
        isLaunching={isLaunching}
        setIsLaunching={setIsLaunching}
        progressState={progressState}
        setProgressState={setProgressState}
      />
      <HowItWorks />
    </>
  );
}

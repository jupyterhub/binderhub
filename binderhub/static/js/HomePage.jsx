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

  useEffect(() => {
    setSpec(`${selectedProvider.id}/${repo}/${ref}`);
  }, [selectedProvider, repo, ref]);

  return (
    <>
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
      />
      <HowItWorks />
    </>
  );
}

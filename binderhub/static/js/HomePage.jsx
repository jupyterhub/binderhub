import { LinkGenerator } from "./components/linkbuilder.jsx";
import { ImageBuilder } from "./components/builder.jsx";
import { HowItWorks } from "./components/howitworks.jsx";
import { useState } from "react";

export default function BinderHomePage({ providers, publicBaseUrl, baseUrl }) {
  const defaultProvider = providers[0];
  const [selectedProvider, setSelectedProvider] = useState(defaultProvider);
  const [repo, setRepo] = useState("");
  const [ref, setRef] = useState("");
  const [urlPath, setUrlPath] = useState("");
  const [isLaunching, setIsLaunching] = useState(false);
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
        selectedProvider={selectedProvider}
        repo={repo}
        reference={ref}
        urlPath={urlPath}
        isLaunching={isLaunching}
        setIsLaunching={setIsLaunching}
      />
      <HowItWorks />
    </>
  );
}

import { createRoot } from "react-dom/client";
import { LinkGenerator } from "./components/linkbuilder.jsx";
import { Header } from "./components/header.jsx";
import { ImageBuilder } from "./components/builder.jsx";
import { HowItWorks } from "./components/howitworks.jsx";
import { useState } from "react";

import "bootstrap/js/dist/dropdown.js";

import "./index.scss";
import "@fontsource/clear-sans/100.css";
import "@fontsource/clear-sans/300.css";
import "@fontsource/clear-sans/400.css";

const PAGE_CONFIG = window.pageConfig;
const PROVIDERS = PAGE_CONFIG.repoProviders;
const baseUrl = new URL(PAGE_CONFIG.baseUrl, window.location.href);
const publicBaseUrl = PAGE_CONFIG.publicBaseUrl
  ? new URL(baseUrl)
  : new URL(PAGE_CONFIG.baseUrl, window.location.href);

export default function BinderHomePage() {
  const defaultProvider = PROVIDERS[0];
  const [selectedProvider, setSelectedProvider] = useState(defaultProvider);
  const [repo, setRepo] = useState("");
  const [ref, setRef] = useState("");
  const [urlPath, setUrlPath] = useState("");
  const [isLaunching, setIsLaunching] = useState(false);
  return (
    <div className="container-md">
      <div className="col-8 offset-md-2">
        <Header
          logoUrl={PAGE_CONFIG.logoUrl}
          logoWidth={PAGE_CONFIG.logoWidth}
        />
        <LinkGenerator
          publicBaseUrl={publicBaseUrl}
          providers={PROVIDERS}
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
      </div>
    </div>
  );
}

const root = createRoot(document.getElementById("root"));
console.log(root);
root.render(<BinderHomePage />);

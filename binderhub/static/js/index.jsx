import { createRoot } from "react-dom/client";

import { Header } from "./components/header.jsx";

import "bootstrap/js/dist/dropdown.js";

import "./index.scss";
import "@fontsource/clear-sans/100.css";
import "@fontsource/clear-sans/300.css";
import "@fontsource/clear-sans/400.css";
import BinderHomePage from "./HomePage.jsx";

export const PAGE_CONFIG = window.pageConfig;
export const PROVIDERS = PAGE_CONFIG.repoProviders;
export const BASE_URL = new URL(PAGE_CONFIG.baseUrl, window.location.href);
export const PUBLIC_BASE_URL = PAGE_CONFIG.publicBaseUrl
  ? new URL(BASE_URL)
  : new URL(PAGE_CONFIG.baseUrl, window.location.href);

function App() {
  return (
    <div className="container-md">
      <div className="col-8 offset-md-2">
        <Header
          logoUrl={PAGE_CONFIG.logoUrl}
          logoWidth={PAGE_CONFIG.logoWidth}
        />
        <BinderHomePage
          providers={PROVIDERS}
          baseUrl={BASE_URL}
          publicBaseUrl={PUBLIC_BASE_URL}
        />
      </div>
    </div>
  );
}

const root = createRoot(document.getElementById("root"));
root.render(<App />);

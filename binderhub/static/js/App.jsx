import { createRoot } from "react-dom/client";

import { LoadingPage } from "./pages/LoadingPage.jsx";
import { createBrowserRouter, RouterProvider, Route } from "react-router-dom";
import "bootstrap/js/dist/dropdown.js";

import "./index.scss";
import "@fontsource/clear-sans/100.css";
import "@fontsource/clear-sans/300.css";
import "@fontsource/clear-sans/400.css";
import { HomePage } from "./pages/HomePage.jsx";
import { createRoutesFromElements } from "react-router";
import { AboutPage } from "./pages/AboutPage.jsx";

export const PAGE_CONFIG = window.pageConfig;

/**
 * @typedef {object} RepoConfig
 * @prop {string} label
 * @prop {string} placeholder
 *
 * @typedef {object} DetectConfig
 * @prop {string} regex
 *
 * @typedef {object} RefConfig
 * @prop {boolean} enabled
 * @prop {string} [default]
 *
 * @typedef {object} Provider
 * @prop {string} displayName
 * @prop {string} id
 * @prop {DetectConfig} [detect]
 * @prop {RepoConfig} repo
 * @prop {RefConfig} ref
 *
 */
/**
 * @type {Array<Provider>}
 */
export const PROVIDERS = PAGE_CONFIG.repoProviders;

export const BASE_URL = new URL(PAGE_CONFIG.baseUrl, window.location.href);

export const PUBLIC_BASE_URL = PAGE_CONFIG.publicBaseUrl
  ? new URL(BASE_URL)
  : new URL(PAGE_CONFIG.baseUrl, window.location.href);

const router = createBrowserRouter(
  createRoutesFromElements(
    <Route>
      <Route
        path={PAGE_CONFIG.baseUrl}
        element={
          <HomePage
            providers={PROVIDERS}
            baseUrl={BASE_URL}
            publicBaseUrl={PUBLIC_BASE_URL}
          />
        }
      />
      {PROVIDERS.map((p) => (
        <Route
          key={p.id}
          path={`${PAGE_CONFIG.baseUrl}v2/*`}
          element={<LoadingPage baseUrl={BASE_URL} />}
        />
      ))}
      <Route
        key="about"
        path={`${PAGE_CONFIG.baseUrl}about`}
        element={
          <AboutPage
            aboutMessage={PAGE_CONFIG.aboutMessage}
            binderVersion={PAGE_CONFIG.binderVersion}
          />
        }
      />
    </Route>,
  ),
);
function App() {
  return (
    <div className="container-md">
      <div className="col-8 offset-md-2">
        <div className="text-center m-4">
          <img src={PAGE_CONFIG.logoUrl} width={PAGE_CONFIG.logoWidth} />
        </div>
        <RouterProvider router={router} />
      </div>
    </div>
  );
}

const root = createRoot(document.getElementById("root"));
root.render(<App />);

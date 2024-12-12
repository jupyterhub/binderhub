import { LoadingPage } from "./pages/LoadingPage.jsx";
import { Route, Routes } from "react-router-dom";
import "bootstrap/js/dist/dropdown.js";

import "./index.scss";
import "@fontsource/clear-sans/100.css";
import "@fontsource/clear-sans/300.css";
import "@fontsource/clear-sans/400.css";
import { HomePage } from "./pages/HomePage.jsx";
import { AboutPage } from "./pages/AboutPage.jsx";
import { NotFoundPage } from "./pages/NotFoundPage.jsx";

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
 * @typedef {object} SpecConfig
 * @prop {string} validateRegex
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

const BUILD_TOKEN = PAGE_CONFIG.buildToken;

export function App() {
  return (
    <>
      {PAGE_CONFIG.bannerHtml && (
        <div
          className="p-3 bg-light shadow-sm text-center"
          dangerouslySetInnerHTML={{ __html: PAGE_CONFIG.bannerHtml }}
        ></div>
      )}
      <div className="container-md">
        <div className="col-8 offset-md-2">
          <div className="text-center m-4">
            <img src={PAGE_CONFIG.logoUrl} width={PAGE_CONFIG.logoWidth} />
          </div>
          <Routes>
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
                path={`${PAGE_CONFIG.baseUrl}v2/${p.id}/*`}
                element={
                  <LoadingPage
                    baseUrl={BASE_URL}
                    buildToken={BUILD_TOKEN}
                    provider={p}
                  />
                }
              />
            ))}
            <Route
              path={`${PAGE_CONFIG.baseUrl}about`}
              element={
                <AboutPage
                  aboutMessage={PAGE_CONFIG.aboutMessage}
                  binderVersion={PAGE_CONFIG.binderVersion}
                />
              }
            />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </div>
      </div>
    </>
  );
}

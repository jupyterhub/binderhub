import { LoadingPage } from "./pages/LoadingPage.jsx";
import { Route, Router, Switch } from "wouter";
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
 * @prop {boolean} urlEncode
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
 * @prop {SpecConfig} spec
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

export function App({ routerHook }) {
  // Wouter's <Router> component requires *not* having trailing slash to function
  // the way we want
  const baseRouteUrl =
    BASE_URL.pathname.slice(-1) == "/"
      ? BASE_URL.pathname.slice(0, -1)
      : BASE_URL.pathname;
  return (
    <>
      {PAGE_CONFIG.bannerHtml && (
        <div
          className="p-3 bg-light shadow-sm text-center"
          dangerouslySetInnerHTML={{ __html: PAGE_CONFIG.bannerHtml }}
        ></div>
      )}
      <div className="container-md">
        <div className="col-10 mx-auto">
          <div className="text-center m-4">
            <img src={PAGE_CONFIG.logoUrl} width={PAGE_CONFIG.logoWidth} />
          </div>
          <Router base={baseRouteUrl} hook={routerHook}>
            <Switch>
              <Route path="/">
                <HomePage
                  providers={PROVIDERS}
                  baseUrl={BASE_URL}
                  publicBaseUrl={PUBLIC_BASE_URL}
                />
              </Route>

              {PROVIDERS.map((p) => (
                <Route
                  key={p.id}
                  path={`/v2/${p.id}/(?<buildSpec>${p.spec.validateRegex})`}
                >
                  <LoadingPage
                    baseUrl={BASE_URL}
                    buildToken={BUILD_TOKEN}
                    provider={p}
                  />
                </Route>
              ))}

              <Route path="/about">
                <AboutPage
                  aboutMessage={PAGE_CONFIG.aboutMessage}
                  binderVersion={PAGE_CONFIG.binderVersion}
                />
              </Route>
              <Route>
                <NotFoundPage />
              </Route>
            </Switch>
          </Router>
        </div>
      </div>
    </>
  );
}

import { render, screen } from "@testing-library/react";

import { App } from "./App";
import { memoryLocation } from "wouter/memory-location";

test("render Homepage", () => {
  render(<App />);
  expect(
    screen.queryByText(
      /Turn a Git repo into a collection of interactive notebooks/,
    ),
  ).toBeInTheDocument();
});

test("render About page", () => {
  const { hook } = memoryLocation({ path: "/about" });
  render(<App routerHook={hook} />);
  expect(screen.queryByText(/This is the about message/)).toBeInTheDocument();
  expect(screen.queryByText(/v123.456/)).toBeInTheDocument();
});

test("render Not Found page", () => {
  const { hook } = memoryLocation({ path: "/not-found" });
  render(<App routerHook={hook} />);
  expect(screen.queryByText(/Not Found/)).toBeInTheDocument();
});

test("renders loading page", () => {
  const { hook } = memoryLocation({ path: "/v2/gh/user/repo/main" });
  render(<App routerHook={hook} />);
  expect(screen.queryByText(/Launching your Binder/)).toBeInTheDocument();
});

test("renders loading page with trailing slash", () => {
  const { hook } = memoryLocation({ path: "/v2/gh/user/repo/main/" });
  render(<App routerHook={hook} />);
  expect(screen.queryByText(/Launching your Binder/)).toBeInTheDocument();
});

test("renders error for misconfigured repo", () => {
  const { hook } = memoryLocation({ path: "/v2/gh/userrep/main/" });
  render(<App routerHook={hook} />);
  expect(screen.queryByText(/Not Found/)).toBeInTheDocument();
});

test("renders loading page with trailing slash", () => {
  const { hook } = memoryLocation({
    path: "/v2/zenodo/10.5281/zenodo.3242074/",
  });
  render(<App routerHook={hook} />);
  expect(screen.queryByText(/Launching your Binder/)).toBeInTheDocument();
});

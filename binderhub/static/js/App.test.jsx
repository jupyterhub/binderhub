import { render, screen } from "@testing-library/react";

import { App } from "./App";
import { MemoryRouter } from "react-router";

test("render Homepage", () => {
  render(
    <MemoryRouter>
      <App />
    </MemoryRouter>,
  );
  expect(
    screen.queryByText(
      /Turn a Git repo into a collection of interactive notebooks/,
    ),
  ).toBeInTheDocument();
});

test("render About page", () => {
  render(
    <MemoryRouter initialEntries={["/about"]}>
      <App />
    </MemoryRouter>,
  );
  expect(screen.queryByText(/This is the about message/)).toBeInTheDocument();
  expect(screen.queryByText(/v123.456/)).toBeInTheDocument();
});

test("render Not Found page", () => {
  render(
    <MemoryRouter initialEntries={["/not-found"]}>
      <App />
    </MemoryRouter>,
  );
  expect(screen.queryByText(/Not Found/)).toBeInTheDocument();
});

test("renders loading page", () => {
  render(
    <MemoryRouter initialEntries={["/v2/gh/user/repo/main"]}>
      <App />
    </MemoryRouter>,
  );
  expect(screen.queryByText(/Launching your Binder/)).toBeInTheDocument();
});

test("renders loading page with trailign slash", () => {
  render(
    <MemoryRouter initialEntries={["/v2/gh/user/repo/main/"]}>
      <App />
    </MemoryRouter>,
  );
  expect(screen.queryByText(/Launching your Binder/)).toBeInTheDocument();
});

test("renders error for misconfigured repo", () => {
  render(
    <MemoryRouter initialEntries={["/v2/gh/userrepo/main"]}>
      <App />
    </MemoryRouter>,
  );
  expect(
    screen.queryByText(
      /Spec is not of the form "user\/repo\/ref", provided: "userrepo\/main"/,
    ),
  ).toBeInTheDocument();
});

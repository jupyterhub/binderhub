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

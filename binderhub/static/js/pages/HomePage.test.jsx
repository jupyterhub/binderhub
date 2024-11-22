import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { HomePage } from "./HomePage";

test("updates launch URL with file", async () => {
  const user = userEvent.setup();

  render(<HomePage
    providers={window.pageConfig.repoProviders}
    baseUrl={"http://local.com"}
    publicBaseUrl={"http://local.com"}
  />);

  expect(screen.getByText(/Fill in the fields to see a URL for sharing your Binder./)).toBeInTheDocument();
  const repositoryField = screen.getByRole("textbox", {name: "Enter repository URL"});
  await user.type(repositoryField, "org/repo");
  expect(screen.getByText("http://local.com/v2/fake/org/repo/undefined")).toBeInTheDocument();

  const fileField = screen.getByRole("textbox", {name: "File to open (in JupyterLab)"});
  await user.type(fileField, "test.py");
  expect(screen.getByText("http://local.com/v2/fake/org/repo/undefined?urlpath=%2Fdoc%2Ftree%2Ftest.py")).toBeInTheDocument();
});

test("updates launch URL with URL", async () => {
  const user = userEvent.setup();

  render(<HomePage
    providers={window.pageConfig.repoProviders}
    baseUrl={"http://local.com"}
    publicBaseUrl={"http://local.com"}
  />);

  expect(screen.getByText(/Fill in the fields to see a URL for sharing your Binder./)).toBeInTheDocument();
  const repositoryField = screen.getByRole("textbox", {name: "Enter repository URL"});
  await user.type(repositoryField, "org/repo");
  expect(screen.getByText("http://local.com/v2/fake/org/repo/undefined")).toBeInTheDocument();

  await(user.click(screen.getByRole("button", {name: "File"})));
  await(user.click(screen.getByText("URL")));

  const fileField = screen.getByRole("textbox", {name: "URL to open"});
  await user.type(fileField, "http://example.com");
  expect(screen.getByText("http://local.com/v2/fake/org/repo/undefined?urlpath=http%3A%2F%2Fexample.com")).toBeInTheDocument();
});

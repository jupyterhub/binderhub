import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { HomePage } from "./HomePage";

test("updates launch URL with git repo", async () => {
  const user = userEvent.setup();

  render(
    <HomePage
      providers={window.pageConfig.repoProviders}
      baseUrl={"http://local.com"}
      publicBaseUrl={"http://local.com"}
    />,
  );

  expect(
    screen.getByText(
      /Fill in the fields to see a URL for sharing your Binder./,
    ),
  ).toBeInTheDocument();
  const repositoryField = screen.getByRole("textbox", {
    name: "Enter repository URL",
  });
  await user.type(repositoryField, "org/repo");
  expect(
    screen.getByText("http://local.com/v2/gh/org/repo/HEAD"),
  ).toBeInTheDocument();
});

test("updates launch URL with git ref", async () => {
  const user = userEvent.setup();

  render(
    <HomePage
      providers={window.pageConfig.repoProviders}
      baseUrl={"http://local.com"}
      publicBaseUrl={"http://local.com"}
    />,
  );

  expect(
    screen.getByText(
      /Fill in the fields to see a URL for sharing your Binder./,
    ),
  ).toBeInTheDocument();
  const repositoryField = screen.getByRole("textbox", {
    name: "Enter repository URL",
  });
  await user.type(repositoryField, "org/repo");
  expect(
    screen.getByText("http://local.com/v2/gh/org/repo/HEAD"),
  ).toBeInTheDocument();

  const refField = screen.getByRole("textbox", {
    name: "Git ref (branch, tag, or commit)",
  });
  await user.type(refField, "main");
  expect(
    screen.getByText("http://local.com/v2/gh/org/repo/main"),
  ).toBeInTheDocument();
});

test("updates launch URL with file", async () => {
  const user = userEvent.setup();

  render(
    <HomePage
      providers={window.pageConfig.repoProviders}
      baseUrl={"http://local.com"}
      publicBaseUrl={"http://local.com"}
    />,
  );

  expect(
    screen.getByText(
      /Fill in the fields to see a URL for sharing your Binder./,
    ),
  ).toBeInTheDocument();
  const repositoryField = screen.getByRole("textbox", {
    name: "Enter repository URL",
  });
  await user.type(repositoryField, "org/repo");
  expect(
    screen.getByText("http://local.com/v2/gh/org/repo/HEAD"),
  ).toBeInTheDocument();

  const fileField = screen.getByRole("textbox", {
    name: "File to open (in JupyterLab)",
  });
  await user.type(fileField, "test.py");
  expect(
    screen.getByText(
      "http://local.com/v2/gh/org/repo/HEAD?urlpath=%2Fdoc%2Ftree%2Ftest.py",
    ),
  ).toBeInTheDocument();
});

test("updates launch URL with URL", async () => {
  const user = userEvent.setup();

  render(
    <HomePage
      providers={window.pageConfig.repoProviders}
      baseUrl={"http://local.com"}
      publicBaseUrl={"http://local.com"}
    />,
  );

  expect(
    screen.getByText(
      /Fill in the fields to see a URL for sharing your Binder./,
    ),
  ).toBeInTheDocument();
  const repositoryField = screen.getByRole("textbox", {
    name: "Enter repository URL",
  });
  await user.type(repositoryField, "org/repo");
  expect(
    screen.getByText("http://local.com/v2/gh/org/repo/HEAD"),
  ).toBeInTheDocument();

  // TODO: There are two buttons name "File" in the DOM, so we need queryAllByRole here.
  // Ideally, these buttons have distinct labels
  await user.click(screen.queryAllByRole("button", { name: "File" })[0]);
  await user.click(screen.getByText("URL"));

  const fileField = screen.getByRole("textbox", { name: "URL to open" });
  await user.type(fileField, "http://example.com");
  expect(
    screen.getByText(
      "http://local.com/v2/gh/org/repo/HEAD?urlpath=http%3A%2F%2Fexample.com",
    ),
  ).toBeInTheDocument();
});

test("change source type", async () => {
  const user = userEvent.setup();

  render(
    <HomePage
      providers={window.pageConfig.repoProviders}
      baseUrl={"http://local.com"}
      publicBaseUrl={"http://local.com"}
    />,
  );

  expect(
    screen.getByText(
      /Fill in the fields to see a URL for sharing your Binder./,
    ),
  ).toBeInTheDocument();
  user.click(screen.getByRole("button", { name: "GitHub" }));

  const zenodoButton = screen.getByRole("button", { name: "Zenodo DOI" });
  await expect(zenodoButton).toBeVisible();

  await user.click(zenodoButton);
  const refField = screen.getByRole("textbox", {
    name: "Git ref (branch, tag, or commit)",
  });
  expect(refField).toBeDisabled();

  const repositoryField = screen.getByRole("textbox", {
    name: "Enter repository URL",
  });
  await user.type(repositoryField, "10.5282/zenodo.3242075");
  expect(
    screen.getByText("http://local.com/v2/zenodo/10.5282/zenodo.3242075/"),
  ).toBeInTheDocument();
});

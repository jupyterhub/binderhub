import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LinkGenerator } from "./LinkGenerator";
import { useState } from "react";

const mockProviders = window.pageConfig.repoProviders;

const publicBaseUrl = new URL("https://example.org/");

function TestLinkGeneratorWrapper() {
  const [selectedProvider, setSelectedProvider] = useState(mockProviders[0]);
  const [repo, setRepo] = useState("");
  const [reference, setReference] = useState("");
  const [urlPath, setUrlPath] = useState("");
  const [isLaunching, setIsLaunching] = useState(false);

  return (
    <LinkGenerator
      providers={mockProviders}
      publicBaseUrl={publicBaseUrl}
      selectedProvider={selectedProvider}
      setSelectedProvider={setSelectedProvider}
      repo={repo}
      setRepo={setRepo}
      reference={reference}
      setReference={setReference}
      urlPath={urlPath}
      setUrlPath={setUrlPath}
      isLaunching={isLaunching}
      setIsLaunching={setIsLaunching}
    />
  );
}

describe("LinkGenerator", () => {
  it("updates launch-url from repo, ref and file", async () => {
    const user = userEvent.setup();
    render(<TestLinkGeneratorWrapper />);

    // This lookup uses the aria label
    const repoInput = screen.getByRole("textbox", {
      name: "Enter repository URL",
    });
    await user.type(repoInput, "my-org/my-repo");

    const refInput = screen.getByLabelText("Git ref (branch, tag, or commit)");
    await user.type(refInput, "my-branch");

    const pathInput = screen.getByLabelText("File to open (in JupyterLab)");
    await user.type(pathInput, "notebooks/test.ipynb");

    const expectedUrl =
      "https://example.org/v2/gh/my-org/my-repo/my-branch?urlpath=%2Fdoc%2Ftree%2Fnotebooks%2Ftest.ipynb";
    expect(screen.getByTestId("launch-url").textContent).toBe(expectedUrl);
  });

  it("renders initial placeholder and restores it if repo is deleted", async () => {
    const user = userEvent.setup();
    render(<TestLinkGeneratorWrapper />);

    const defaultLaunchUrl =
      "Fill in the fields to see a URL for sharing your Binder.";
    expect(screen.getByTestId("launch-url").textContent).toBe(defaultLaunchUrl);

    const repoInput = screen.getByRole("textbox", {
      name: "Enter repository URL",
    });
    await user.type(repoInput, "x");

    expect(screen.getByTestId("launch-url").textContent).toBe(
      "https://example.org/v2/gh/x/HEAD",
    );

    await user.type(repoInput, "{backspace}");
    expect(screen.getByTestId("launch-url").textContent).toBe(defaultLaunchUrl);
  });
});

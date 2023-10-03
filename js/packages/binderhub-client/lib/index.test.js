import { BinderRepository } from ".";

test("Passed in URL object is not modified", () => {
  const buildEndpointUrl = new URL("https://test-binder.org/build");
  const br = new BinderRepository("gh/test/test", buildEndpointUrl, "token");
  expect(br.buildEndpointUrl.toString()).not.toEqual(
    buildEndpointUrl.toString()
  );
});

test("Invalid URL errors out", () => {
  expect(() => {
    new BinderRepository("gh/test/test", "/build", "token");
  }).toThrow(TypeError);
});

test("Trailing slash added if needed", () => {
  const buildEndpointUrl = new URL("https://test-binder.org/build");
  const br = new BinderRepository("gh/test/test", buildEndpointUrl);
  expect(br.buildEndpointUrl.toString()).toEqual(
    "https://test-binder.org/build/"
  );
});

test("Build URL correctly built from Build Endpoint", () => {
  const buildEndpointUrl = new URL("https://test-binder.org/build");
  const br = new BinderRepository("gh/test/test", buildEndpointUrl);
  expect(br.buildUrl.toString()).toEqual(
    "https://test-binder.org/build/gh/test/test"
  );
});

test("Build URL correctly built from Build Endpoint when used with token", () => {
  const buildEndpointUrl = new URL("https://test-binder.org/build");
  const br = new BinderRepository("gh/test/test", buildEndpointUrl, "token");
  expect(br.buildUrl.toString()).toEqual(
    "https://test-binder.org/build/gh/test/test?build_token=token"
  );
});

test("Get full redirect URL with correct token but no path", () => {
  const br = new BinderRepository(
    "gh/test/test",
    new URL("https://test-binder.org/build")
  );
  expect(
    br
      .getFullRedirectURL("https://hub.test-binder.org/user/something", "token")
      .toString()
  ).toBe("https://hub.test-binder.org/user/something?token=token");
});

test("Get full redirect URL with urlpath", () => {
  const br = new BinderRepository(
    "gh/test/test",
    new URL("https://test-binder.org/build")
  );
  expect(
    br
      .getFullRedirectURL(
        "https://hub.test-binder.org/user/something",
        "token",
        "rstudio",
        "url"
      )
      .toString()
  ).toBe("https://hub.test-binder.org/user/something/rstudio?token=token");
});

test("Get full redirect URL when opening a file with jupyterlab", () => {
  const br = new BinderRepository(
    "gh/test/test",
    new URL("https://test-binder.org/build")
  );
  expect(
    br
      .getFullRedirectURL(
        "https://hub.test-binder.org/user/something",
        "token",
        "index.ipynb",
        "lab"
      )
      .toString()
  ).toBe("https://hub.test-binder.org/user/something/doc/tree/index.ipynb?token=token");
});

test("Get full redirect URL when opening a file with classic notebook (with file= path)", () => {
  const br = new BinderRepository(
    "gh/test/test",
    new URL("https://test-binder.org/build")
  );
  expect(
    br
      .getFullRedirectURL(
        "https://hub.test-binder.org/user/something",
        "token",
        "index.ipynb",
        "file"
      )
      .toString()
  ).toBe("https://hub.test-binder.org/user/something/tree/index.ipynb?token=token");
});

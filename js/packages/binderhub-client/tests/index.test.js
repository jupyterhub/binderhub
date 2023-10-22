import {
  BinderRepository,
  makeShareableBinderURL,
  makeBadgeMarkup,
} from "@jupyterhub/binderhub-client";
import { parseEventSource, simpleEventSourceServer } from "./utils";
import { readFileSync } from "node:fs";

test("Passed in URL object is not modified", () => {
  const buildEndpointUrl = new URL("https://test-binder.org/build");
  const br = new BinderRepository("gh/test/test", buildEndpointUrl, "token");
  expect(br.buildEndpointUrl.toString()).not.toEqual(
    buildEndpointUrl.toString(),
  );
});

test("Invalid URL errors out", () => {
  expect(() => {
    new BinderRepository("gh/test/test", "/build", "token");
  }).toThrow(TypeError);
});

test("Passing buildOnly flag works", () => {
  const buildEndpointUrl = new URL("https://test-binder.org/build");
  const br = new BinderRepository("gh/test/test", buildEndpointUrl, null, true);
  expect(br.buildUrl.toString()).toEqual(
    "https://test-binder.org/build/gh/test/test?build_only=true",
  );
});

test("Trailing slash added if needed", () => {
  const buildEndpointUrl = new URL("https://test-binder.org/build");
  const br = new BinderRepository("gh/test/test", buildEndpointUrl);
  expect(br.buildEndpointUrl.toString()).toEqual(
    "https://test-binder.org/build/",
  );
});

test("Build URL correctly built from Build Endpoint", () => {
  const buildEndpointUrl = new URL("https://test-binder.org/build");
  const br = new BinderRepository("gh/test/test", buildEndpointUrl);
  expect(br.buildUrl.toString()).toEqual(
    "https://test-binder.org/build/gh/test/test",
  );
});

test("Build URL correctly built from Build Endpoint when used with token", () => {
  const buildEndpointUrl = new URL("https://test-binder.org/build");
  const br = new BinderRepository("gh/test/test", buildEndpointUrl, "token");
  expect(br.buildUrl.toString()).toEqual(
    "https://test-binder.org/build/gh/test/test?build_token=token",
  );
});

test("Get full redirect URL with correct token but no path", () => {
  const br = new BinderRepository(
    "gh/test/test",
    new URL("https://test-binder.org/build"),
  );
  expect(
    br
      .getFullRedirectURL(
        new URL("https://hub.test-binder.org/user/something"),
        "token",
      )
      .toString(),
  ).toBe("https://hub.test-binder.org/user/something?token=token");
});

test("Get full redirect URL with urlpath", () => {
  const br = new BinderRepository(
    "gh/test/test",
    new URL("https://test-binder.org/build"),
  );
  expect(
    br
      .getFullRedirectURL(
        new URL("https://hub.test-binder.org/user/something"),
        "token",
        "rstudio",
        "url",
      )
      .toString(),
  ).toBe("https://hub.test-binder.org/user/something/rstudio?token=token");
});

test("Get full redirect URL when opening a file with jupyterlab", () => {
  const br = new BinderRepository(
    "gh/test/test",
    new URL("https://test-binder.org/build"),
  );
  expect(
    br
      .getFullRedirectURL(
        new URL("https://hub.test-binder.org/user/something"),
        "token",
        "index.ipynb",
        "lab",
      )
      .toString(),
  ).toBe(
    "https://hub.test-binder.org/user/something/doc/tree/index.ipynb?token=token",
  );
});

test("Get full redirect URL when opening a file with classic notebook (with file= path)", () => {
  const br = new BinderRepository(
    "gh/test/test",
    new URL("https://test-binder.org/build"),
  );
  expect(
    br
      .getFullRedirectURL(
        new URL("https://hub.test-binder.org/user/something"),
        "token",
        "index.ipynb",
        "file",
      )
      .toString(),
  ).toBe(
    "https://hub.test-binder.org/user/something/tree/index.ipynb?token=token",
  );
});

test("Get full redirect URL and deal with excessive slashes (with pathType=url)", () => {
  const br = new BinderRepository(
    "gh/test/test",
    new URL("https://test-binder.org/build"),
  );
  expect(
    br
      .getFullRedirectURL(
        // Trailing slash should not be preserved here
        new URL("https://hub.test-binder.org/user/something/"),
        "token",
        // Trailing slash should be preserved here, but leading slash should not be repeated
        "/rstudio/",
        "url",
      )
      .toString(),
  ).toBe("https://hub.test-binder.org/user/something/rstudio/?token=token");
});

test("Get full redirect URL and deal with excessive slashes (with pathType=lab)", () => {
  const br = new BinderRepository(
    "gh/test/test",
    new URL("https://test-binder.org/build"),
  );
  expect(
    br
      .getFullRedirectURL(
        new URL("https://hub.test-binder.org/user/something/"),
        "token",
        // Both leading and trailing slashes should be gone here.
        "/directory/index.ipynb/",
        "lab",
      )
      .toString(),
  ).toBe(
    "https://hub.test-binder.org/user/something/doc/tree/directory/index.ipynb?token=token",
  );
});

test("Get full redirect URL and deal with missing trailing slash", () => {
  const br = new BinderRepository(
    "gh/test/test",
    new URL("https://test-binder.org/build"),
  );
  expect(
    br
      .getFullRedirectURL(
        // Missing trailing slash here should not affect target url
        new URL("https://hub.test-binder.org/user/something"),
        "token",
        "/directory/index.ipynb/",
        "lab",
      )
      .toString(),
  ).toBe(
    "https://hub.test-binder.org/user/something/doc/tree/directory/index.ipynb?token=token",
  );
});

test("Get full redirect URL and deal with excessive slashes (with pathType=file)", () => {
  const br = new BinderRepository(
    "gh/test/test",
    new URL("https://test-binder.org/build"),
  );
  expect(
    br
      .getFullRedirectURL(
        new URL("https://hub.test-binder.org/user/something/"),
        "token",
        // Both leading and trailing slashes should be gone here.
        "/directory/index.ipynb/",
        "file",
      )
      .toString(),
  ).toBe(
    "https://hub.test-binder.org/user/something/tree/directory/index.ipynb?token=token",
  );
});

describe("Iterate over full output from calling the binderhub API", () => {
  let closeServer, serverUrl;

  let responseContents = readFileSync(
    `${__dirname}/fixtures/fullbuild.eventsource`,
    { encoding: "utf-8" },
  );
  beforeEach(async () => {
    [serverUrl, closeServer] = await simpleEventSourceServer({
      "/build/gh/test/test": responseContents,
    });
    console.log(serverUrl);
  });

  afterEach(() => closeServer());
  test("Iterate over full output from fetch", async () => {
    let i = 0;
    const buildEndpointUrl = new URL(`${serverUrl}/build`);
    const br = new BinderRepository("gh/test/test", buildEndpointUrl);
    const messages = parseEventSource(responseContents);
    for await (const item of br.fetch()) {
      expect(item).toStrictEqual(messages[i]);
      i += 1;
      if (item.phase && item.phase === "ready") {
        br.close();
      }
    }
  });
});

describe("Invalid eventsource response causes failure", () => {
  let closeServer, serverUrl;

  beforeEach(async () => {
    [serverUrl, closeServer] = await simpleEventSourceServer({
      "/build/gh/test/test": "invalid",
    });
  });

  afterEach(() => closeServer());
  test("Invalid eventsource response should cause failure", async () => {
    const buildEndpointUrl = new URL(`${serverUrl}/build`);
    const br = new BinderRepository("gh/test/test", buildEndpointUrl);
    for await (const item of br.fetch()) {
      expect(item).toStrictEqual({
        phase: "failed",
        message: "Failed to connect to event stream\n",
      });
    }
  });
});

test("Get full redirect URL and deal with query and encoded query (with pathType=url)", () => {
  const br = new BinderRepository(
    "gh/test/test",
    new URL("https://test-binder.org/build"),
  );
  expect(
    br
      .getFullRedirectURL(
        new URL("https://hub.test-binder.org/user/something/"),
        "token",
        // url path here is already url encoded
        "endpoint?a=1%2F2&b=3%3F%2F",
        "url",
      )
      .toString(),
  ).toBe(
    // url path here is exactly as encoded as passed in - not *double* encoded
    "https://hub.test-binder.org/user/something/endpoint?a=1%2F2&b=3%3F%2F&token=token",
  );
});

test("Get full redirect URL with nbgitpuller URL", () => {
  const br = new BinderRepository(
    "gh/test/test",
    new URL("https://test-binder.org/build"),
  );
  expect(
    br
      .getFullRedirectURL(
        new URL("https://hub.test-binder.org/user/something/"),
        "token",
        // urlpath is not actually url encoded - note that / is / not %2F
        "git-pull?repo=https://github.com/alperyilmaz/jupyterlab-python-intro&urlpath=lab/tree/jupyterlab-python-intro/&branch=master",
        "url",
      )
      .toString(),
  ).toBe(
    // generated URL path here *is* url encoded
    "https://hub.test-binder.org/user/something/git-pull?repo=https%3A%2F%2Fgithub.com%2Falperyilmaz%2Fjupyterlab-python-intro&urlpath=lab%2Ftree%2Fjupyterlab-python-intro%2F&branch=master&token=token",
  );
});

test("Make a shareable URL", () => {
  const url = makeShareableBinderURL(
    new URL("https://test.binder.org"),
    "gh",
    "yuvipanda",
    "requirements",
  );
  expect(url.toString()).toBe(
    "https://test.binder.org/v2/gh/yuvipanda/requirements",
  );
});

test("Make a shareable path with URL", () => {
  const url = makeShareableBinderURL(
    new URL("https://test.binder.org"),
    "gh",
    "yuvipanda",
    "requirements",
    "url",
    "git-pull?repo=https://github.com/alperyilmaz/jupyterlab-python-intro&urlpath=lab/tree/jupyterlab-python-intro/&branch=master",
  );
  expect(url.toString()).toBe(
    "https://test.binder.org/v2/gh/yuvipanda/requirements?git-pull%3Frepo%3Dhttps%3A%2F%2Fgithub.com%2Falperyilmaz%2Fjupyterlab-python-intro%26urlpath%3Dlab%2Ftree%2Fjupyterlab-python-intro%2F%26branch%3Dmasterpath=url",
  );
});

test("Making a shareable URL with base URL without trailing / throws error", () => {
  expect(() => {
    makeShareableBinderURL(
      new URL("https://test.binder.org/suffix"),
      "gh",
      "yuvipanda",
      "requirements",
    );
  }).toThrow(Error);
});

test("Make a markdown badge", () => {
  const url = makeShareableBinderURL(
    new URL("https://test.binder.org"),
    "gh",
    "yuvipanda",
    "requirements",
  );
  const badge = makeBadgeMarkup(
    new URL("https://test.binder.org"),
    url,
    "markdown",
  );
  expect(badge).toBe(
    "[![Binder](https://test.binder.org/badge_logo.svg)](https://test.binder.org/v2/gh/yuvipanda/requirements)",
  );
});

test("Make a rst badge", () => {
  const url = makeShareableBinderURL(
    new URL("https://test.binder.org"),
    "gh",
    "yuvipanda",
    "requirements",
  );
  const badge = makeBadgeMarkup(new URL("https://test.binder.org"), url, "rst");
  expect(badge).toBe(
    ".. image:: https://test.binder.org/badge_logo.svg\n :target: https://test.binder.org/v2/gh/yuvipanda/requirements",
  );
});

test("Making a badge with an unsupported syntax throws error", () => {
  const url = makeShareableBinderURL(
    new URL("https://test.binder.org"),
    "gh",
    "yuvipanda",
    "requirements",
  );
  expect(() => {
    makeBadgeMarkup(new URL("https://test.binder.org"), url, "docx");
  }).toThrow(Error);
});

test("Making a badge with base URL without trailing / throws error", () => {
  const url = makeShareableBinderURL(
    new URL("https://test.binder.org"),
    "gh",
    "yuvipanda",
    "requirements",
  );
  expect(() => {
    makeBadgeMarkup(new URL("https://test.binder.org/suffix"), url, "markdown");
  }).toThrow(Error);
});

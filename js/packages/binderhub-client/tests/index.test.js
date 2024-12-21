// fetch polyfill (only needed for node tests)
import { fetch, TextDecoder } from "@whatwg-node/fetch";

import { BinderRepository } from "@jupyterhub/binderhub-client";
import { parseEventSource, simpleEventSourceServer } from "./utils";
import { readFileSync } from "node:fs";

async function wrapFetch(resource, options) {
  /* like fetch, but ignore signal input
  // abort signal shows up as uncaught in tests, despite  working fine
  */
  if (options) {
    options.signal = null;
  }
  return fetch.apply(null, [resource, options]);
}

beforeAll(() => {
  // inject globals for fetch
  global.TextDecoder = TextDecoder;
  if (!global.window) {
    global.window = {};
  }
  if (!global.window.fetch) {
    global.window.fetch = wrapFetch;
  }
});

test("Passed in URL object is not modified", () => {
  const buildEndpointUrl = new URL("https://test-binder.org/build");
  const br = new BinderRepository("gh/test/test", buildEndpointUrl, {
    buildToken: "token",
  });
  expect(br.buildEndpointUrl.toString()).not.toEqual(
    buildEndpointUrl.toString(),
  );
});

test("Invalid URL errors out", () => {
  expect(() => {
    new BinderRepository("gh/test/test", "/build", { buildToken: "token" });
  }).toThrow(TypeError);
});

test("Passing buildOnly flag works", () => {
  const buildEndpointUrl = new URL("https://test-binder.org/build");
  const br = new BinderRepository("gh/test/test", buildEndpointUrl, {
    buildOnly: true,
  });
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
  const br = new BinderRepository("gh/test/test", buildEndpointUrl, {
    buildToken: "token",
  });
  expect(br.buildUrl.toString()).toEqual(
    "https://test-binder.org/build/gh/test/test?build_token=token",
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
    let messages = [];
    for await (const item of br.fetch()) {
      messages.push(item);
    }
    expect(messages).toStrictEqual([
      {
        phase: "failed",
        message: "Event stream closed unexpectedly\n",
      },
    ]);
  });
});

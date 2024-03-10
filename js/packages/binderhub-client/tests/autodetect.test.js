import { getRepoProviders, detect } from "../lib/autodetect";
import { readFileSync } from "node:fs";

const mybinderConfig = JSON.parse(
  readFileSync(`${__dirname}/fixtures/repoprovider-config.json`, {
    encoding: "utf-8",
  }),
);

// Mock fetch()
// https://www.leighhalliday.com/mock-fetch-jest
global.fetch = jest.fn((url) => {
  if (url == "https://binder.example.org/_config") {
    return Promise.resolve({
      json: () => Promise.resolve(mybinderConfig),
    });
  }
  return Promise.reject(`Unexpected URL ${url}`);
});

beforeEach(() => {
  fetch.mockClear();
});

test("getRepoProviders requests and caches the repo provider configs", async () => {
  const config = await getRepoProviders("https://binder.example.org");
  expect(config).toEqual(mybinderConfig);

  await getRepoProviders("https://binder.example.org");
  expect(fetch).toHaveBeenCalledTimes(1);
});

test("detect returns null if no provider matches", async () => {
  const result = await detect(
    "https://binder.example.org",
    "https://github.com/binder-examples/conda/pulls",
  );
  expect(result).toBeNull();
});

test("detect parses a repo with no path", async () => {
  const expected = {
    providerPrefix: "gh",
    repository: "binder-examples/conda",
    ref: null,
    path: null,
    pathType: null,
    providerName: "GitHub",
  };
  const result = await detect(
    "https://binder.example.org",
    "https://github.com/binder-examples/conda",
  );
  expect(result).toEqual(expected);
});

test("detect parses a repo with a ref but no path", async () => {
  const expected = {
    providerPrefix: "gh",
    repository: "binder-examples/conda",
    ref: "abc",
    path: null,
    pathType: null,
    providerName: "GitHub",
  };
  const result = await detect(
    "https://binder.example.org",
    "https://github.com/binder-examples/conda/tree/abc",
  );
  expect(result).toEqual(expected);
});

test("detect parses a repo with a ref and file path", async () => {
  const expected = {
    providerPrefix: "gh",
    repository: "binder-examples/conda",
    ref: "f00a783",
    path: "index.ipynb",
    pathType: "filepath",
    providerName: "GitHub",
  };
  const result = await detect(
    "https://binder.example.org",
    "https://github.com/binder-examples/conda/blob/f00a783/index.ipynb",
  );
  expect(result).toEqual(expected);
});

test("detect parses a repo with a ref and directory path", async () => {
  const expected = {
    providerPrefix: "gh",
    repository: "binder-examples/conda",
    ref: "f00a783",
    path: ".github/workflows",
    pathType: "urlpath",
    providerName: "GitHub",
  };
  const result = await detect(
    "https://binder.example.org",
    "https://github.com/binder-examples/conda/tree/f00a783/.github/workflows",
  );
  expect(result).toEqual(expected);
});

test("detect checks other repo providers", async () => {
  const expected = {
    providerPrefix: "gl",
    repository: "gitlab-org/gitlab-foss",
    ref: "v16.4.4",
    path: "README.md",
    pathType: "filepath",
    providerName: "GitLab.com",
  };
  const result = await detect(
    "https://binder.example.org",
    "https://gitlab.com/gitlab-org/gitlab-foss/-/blob/v16.4.4/README.md",
  );
  expect(result).toEqual(expected);
});

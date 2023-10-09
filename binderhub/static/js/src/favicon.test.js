import { updateFavicon } from "./favicon";

afterEach(() => {
  // Clear out HEAD after each test run, so our DOM is clean.
  // Jest does *not* clear out the DOM between test runs on the same file!
  document.querySelector("head").innerHTML = "";
});

test("Setting favicon when there is none works", () => {
  expect(document.querySelector("link[rel*='icon']")).toBeNull();

  updateFavicon("https://example.com/somefile.png");

  expect(document.querySelector("link[rel*='icon']").href).toBe(
    "https://example.com/somefile.png",
  );
});

test("Setting favicon multiple times works without leaking link tags", () => {
  expect(document.querySelector("link[rel*='icon']")).toBeNull();

  updateFavicon("https://example.com/somefile.png");

  expect(document.querySelector("link[rel*='icon']").href).toBe(
    "https://example.com/somefile.png",
  );
  expect(document.querySelectorAll("link[rel*='icon']").length).toBe(1);

  updateFavicon("https://example.com/some-other-file.png");

  expect(document.querySelector("link[rel*='icon']").href).toBe(
    "https://example.com/some-other-file.png",
  );
  expect(document.querySelectorAll("link[rel*='icon']").length).toBe(1);
});

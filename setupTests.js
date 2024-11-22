import { jest } from "@jest/globals";
import "@testing-library/jest-dom";

HTMLCanvasElement.prototype.getContext = () => {};
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // Deprecated
    removeListener: jest.fn(), // Deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

window.pageConfig = {
  repoProviders: [
    {
      "displayName": "Fake",
      "enabled": false,
      "id": "fake",
      "ref": {
          "enabled": false
      },
      "repo": {
          "label": "Fake Repo",
          "placeholder": ""
      }
    }
  ]
}

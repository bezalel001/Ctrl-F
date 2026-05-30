import { readdir, readFile } from "node:fs/promises";
import { join } from "node:path";

const distDir = new URL("../dist/", import.meta.url);
const assetsDir = new URL("../dist/assets/", import.meta.url);

const indexHtml = await readFile(new URL("index.html", distDir), "utf8");
const assets = await readdir(assetsDir);
const jsAsset = assets.find((asset) => asset.endsWith(".js"));
const cssAsset = assets.find((asset) => asset.endsWith(".css"));

assert(jsAsset, "missing built JavaScript asset");
assert(cssAsset, "missing built CSS asset");
assert(indexHtml.includes("/assets/"), "index.html does not reference built assets");

const jsBundle = await readFile(join(assetsDir.pathname, jsAsset), "utf8");
const cssBundle = await readFile(join(assetsDir.pathname, cssAsset), "utf8");

[
  "Company Knowledge",
  "Sign in",
  "Ask a company question",
  "Source Registry",
  "Edit Source",
  "Feedback",
  "Max confidence",
  "Helpful",
  "Not helpful",
  "Ctrl-F is typing",
].forEach((text) => {
  assert(jsBundle.includes(text), `missing UI text in bundle: ${text}`);
});

[
  ".content-grid",
  ".chat-panel",
  ".source-admin-list",
  ".feedback-filter-form",
  ".typing-indicator",
  "@keyframestyping-pulse",
  "@media(max-width:820px)",
].forEach((selector) => {
  assert(cssBundle.replaceAll(" ", "").includes(selector), `missing CSS selector in bundle: ${selector}`);
});

console.log("Frontend smoke check passed.");

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

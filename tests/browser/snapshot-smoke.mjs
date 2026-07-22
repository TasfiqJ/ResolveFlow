import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const html = await readFile("apps/web/out/index.html", "utf8");
assert.match(html, /Slack-style simulation/);
assert.match(html, /Recorded fixture/);
assert.match(html, /Payments Platform/);
assert.match(html, /cluster ID is not available/i);
assert.doesNotMatch(html, /Run live with Cohere/);
console.log("Snapshot browser smoke passed.");


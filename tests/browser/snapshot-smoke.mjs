import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const html = await readFile("apps/web/out/index.html", "utf8");
assert.match(html, /Slack-style simulation/);
assert.match(html, /Recorded run/);
assert.match(html, /Payments Platform/);
assert.match(html, /cluster ID is not available/i);
assert.doesNotMatch(html, /Run live with Cohere/);
for (const route of [
  "demo",
  "replay",
  "results",
  "architecture",
  "methodology",
  "about",
  "review",
  "runs/run_hero_foundation_001",
]) {
  const routeHtml = await readFile(`apps/web/out/${route}/index.html`, "utf8");
  assert.match(routeHtml, /ResolveFlow/);
}
const review = await readFile("apps/web/out/review/index.html", "utf8");
assert.match(review, /OUTPUT A/);
assert.match(review, /OUTPUT B/);
assert.doesNotMatch(review, /unsafe-v0|guarded-v1/);
const replay = await readFile("apps/web/out/replay/index.html", "utf8");
assert.match(replay, /RECORDED/);
assert.match(replay, /Live mode off/);
assert.match(replay, /complete checksummed recorded comparison/);
const results = await readFile("apps/web/out/results/index.html", "utf8");
assert.match(results, /0 reviewers \/ 0 cases/);
console.log("Snapshot browser smoke passed.");

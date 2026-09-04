import assert from "node:assert/strict";
import { access, readdir, readFile } from "node:fs/promises";
import { extname, join, relative, resolve } from "node:path";

const outputRoot = "apps/web/out";
const deploymentPath = "/ResolveFlow";
const deploymentUrl = new URL(`${deploymentPath}/`, "https://resolveflow.test");

async function exportedHtmlFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(
    entries.map((entry) => {
      const path = join(directory, entry.name);
      return entry.isDirectory()
        ? exportedHtmlFiles(path)
        : Promise.resolve(entry.name.endsWith(".html") ? [path] : []);
    }),
  );
  return nested.flat();
}

async function assertInternalExportedLinksResolve() {
  const broken = [];
  for (const sourcePath of await exportedHtmlFiles(outputRoot)) {
    const source = await readFile(sourcePath, "utf8");
    const sourceRelative = relative(outputRoot, sourcePath).replaceAll("\\", "/");
    const sourceUrl = new URL(sourceRelative.replace(/index\.html$/, ""), deploymentUrl);
    const baseHref = source.match(/<base\s+[^>]*href="([^"]+)"/i)?.[1];
    const documentUrl = baseHref ? new URL(baseHref, sourceUrl) : sourceUrl;
    for (const [, rawHref] of source.matchAll(/href="([^"]+)"/g)) {
      if (
        rawHref.startsWith("#") ||
        /^(?:https?:|mailto:|tel:|data:|javascript:)/.test(rawHref)
      ) {
        continue;
      }

      const targetUrl = new URL(rawHref, documentUrl);
      const pathname = decodeURIComponent(targetUrl.pathname).replace(/\/$/, "");
      if (pathname !== deploymentPath && !pathname.startsWith(`${deploymentPath}/`)) {
        broken.push(`${relative(outputRoot, sourcePath)} -> ${rawHref} (outside base path)`);
        continue;
      }
      const exportPath = pathname.slice(deploymentPath.length).replace(/^\//, "");
      if (!exportPath) continue;

      const resolvedExportPath = resolve(outputRoot, exportPath);
      const targetPath = extname(exportPath)
        ? resolvedExportPath
        : join(resolvedExportPath, "index.html");
      try {
        await access(targetPath);
      } catch {
        broken.push(
          `${relative(outputRoot, sourcePath)} -> ${rawHref} (${relative(outputRoot, targetPath)})`,
        );
      }
    }
  }
  assert.deepEqual(
    broken,
    [],
    `Broken internal exported links:\n${broken.join("\n")}`,
  );
}

const html = await readFile("apps/web/out/index.html", "utf8");
assert.match(html, /I BUILT THE/);
assert.match(html, /RELEASE GATE/);
assert.match(html, /BUILT END-TO-END BY TASFIQ JASIMUDDIN/);
assert.match(html, /14-EVENT RECORDED SYNTHETIC TRACE/);
assert.match(html, /Technical preview/);
assert.match(html, /0 reviewers \/ 0 cases/i);
assert.match(html, /Payments Platform/);
assert.match(html, /cluster ID is not available/i);
assert.match(html, /THE RECEIPTS, NOT THE PITCH/);
assert.doesNotMatch(html, /Run live with Cohere/);
for (const route of [
  "demo",
  "replay",
  "results",
  "architecture",
  "cohere",
  "methodology",
  "about",
  "audit",
  "review",
  "runs/run_hero_foundation_001",
]) {
  const routeHtml = await readFile(`apps/web/out/${route}/index.html`, "utf8");
  assert.match(routeHtml, /ResolveFlow/);
}
await assertInternalExportedLinksResolve();
const review = await readFile("apps/web/out/review/index.html", "utf8");
assert.match(review, /OUTPUT A/);
assert.match(review, /OUTPUT B/);
assert.doesNotMatch(review, /unsafe-v0|guarded-v1/);
const replay = await readFile("apps/web/out/replay/index.html", "utf8");
assert.match(replay, /RECORDED/);
assert.match(replay, /LIVE INFERENCE/);
assert.match(replay, /complete checksummed recorded comparison/);
assert.match(replay, /Know what is recorded/);
const results = await readFile("apps/web/out/results/index.html", "utf8");
assert.match(results, /0 reviewers \/ 0 cases/);
assert.match(results, /technical preview only/i);
const abResults = await readFile("apps/web/out/results/ab/index.html", "utf8");
const abVisibleText = abResults.replaceAll("<!-- -->", "");
assert.match(abVisibleText, /Live Cohere, guarded vs unguarded,.*32.*runs/i);
assert.match(abVisibleText, /16.*unsafe-v0.*16.*guarded-v1/i);
assert.match(abVisibleText, /Quality validity:.*VOID/i);
assert.doesNotMatch(abVisibleText, /No live Cohere run has been performed/i);
console.log("Snapshot browser smoke passed.");

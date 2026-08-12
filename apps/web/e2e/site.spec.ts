import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import liveSnapshot from "../public/snapshots/hero-cohere-live.json";

const basePath = (process.env.NEXT_PUBLIC_BASE_PATH ?? "").replace(/\/+$/, "");
const deployedPath = (route: string) => `${basePath}${route}`;

test.beforeEach(async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
});

test("homepage leads to evidence instead of decorative dead ends", async ({
  page,
}) => {
  await page.goto(deployedPath("/"));

  await expect(
    page.getByRole("heading", {
      name: "I BUILT THE RELEASE GATE AI AGENTS ARE MISSING.",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: /stored attack payloads/i }),
  ).toHaveAttribute("href", /evaluation-integrity-audit\.json/);

  await page.getByRole("link", { name: "Replay", exact: true }).click();
  await expect(page).toHaveURL(/\/replay\/$/);
  await expect(
    page.getByRole("heading", { name: "Change the world, not the question." }),
  ).toBeVisible();
});

test("scenario evidence changes without pretending tests are recorded runs", async ({
  page,
}) => {
  await page.goto(deployedPath("/replay/"));

  await expect(
    page.getByRole("heading", {
      name: "Restricted evidence is removed before ranking.",
    }),
  ).toBeVisible();

  await page.getByRole("tab", { name: /Malicious runbook/i }).click();
  await expect(
    page.getByRole("heading", {
      name: "Evidence text cannot widen tools, policy, or action authority.",
    }),
  ).toBeVisible();
  await expect(
    page.getByText(/No separate public run snapshot has been published/i),
  ).toBeVisible();

  await page.getByRole("tab", { name: /Jira outage/i }).click();
  await expect(
    page.getByRole("definition").filter({ hasText: /not a live integration/i }),
  ).toBeVisible();
});

test("keyboard navigation exposes the skip link", async ({ page }) => {
  await page.goto(deployedPath("/"));
  await page.keyboard.press("Tab");

  const skipLink = page.getByRole("link", { name: "Skip to content" });
  await expect(skipLink).toBeFocused();
  await skipLink.press("Enter");
  await expect(page).toHaveURL(/#main-content$/);
});

test("global navigation works from a nested deployment route", async ({
  page,
}) => {
  await page.goto(deployedPath("/results/"));
  await page.getByRole("link", { name: "Replay", exact: true }).click();
  await expect(page).toHaveURL(/\/replay\/$/);

  await page.getByRole("link", { name: "ResolveFlow home" }).click();
  await expect(page).toHaveURL(new RegExp(`${basePath || ""}/$`));
});

test("published live-provider trace exposes exact verified citations and hash links", async ({
  page,
}) => {
  await page.goto(
    deployedPath(`/runs/${liveSnapshot.run_id}/`),
  );

  await expect(
    page.getByText("LIVE-PROVIDER RUN · SYNTHETIC DATA · NO SHIP"),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "Verified citations" })).toBeVisible();
  await expect(page.getByText("citation_supports_claim", { exact: false })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Full hash-linked audit trace" }),
  ).toBeVisible();
  await expect(page.getByText(/event sha256:/).first()).toBeVisible();
  await expect(page.getByText(/no real Slack or Jira write/i)).toBeVisible();
});

for (const route of ["/", "/replay/", "/results/", "/audit/"]) {
  test(`${route} has no automatically detectable WCAG A/AA violations`, async ({
    page,
  }) => {
    await page.goto(deployedPath(route));
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
      .analyze();

    const summary = results.violations.map((violation) => ({
      id: violation.id,
      targets: violation.nodes.map((node) => node.target),
    }));
    expect(results.violations, JSON.stringify(summary, null, 2)).toEqual([]);
  });
}

test("mobile homepage and Replay do not overflow horizontally", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });

  for (const route of ["/", "/replay/"]) {
    await page.goto(deployedPath(route));
    const dimensions = await page.evaluate(() => ({
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
    }));
    expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
  }
});

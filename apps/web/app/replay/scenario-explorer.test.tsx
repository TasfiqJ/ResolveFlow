import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import ScenarioExplorer from "./scenario-explorer";

describe("scenario evidence explorer", () => {
  it("distinguishes published snapshots from test-only evidence", () => {
    render(<ScenarioExplorer />);

    expect(
      screen.getByRole("heading", {
        name: /restricted evidence is removed before ranking/i,
      }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: /malicious runbook/i }));

    expect(
      screen.getByRole("heading", {
        name: /evidence text cannot widen tools/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/no separate public run snapshot has been published/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /review the security test/i }),
    ).toHaveAttribute(
      "href",
      expect.stringContaining("test_evidence_cannot_mutate_policy.py"),
    );

    fireEvent.keyDown(screen.getByRole("tab", { name: /malicious runbook/i }), {
      key: "ArrowRight",
    });
    expect(
      screen.getByRole("heading", {
        name: /missing decisive evidence forces review/i,
      }),
    ).toBeInTheDocument();
  });
});

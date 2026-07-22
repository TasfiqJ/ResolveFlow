import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import Home from "./page";

describe("snapshot-first home", () => {
  it("labels synthetic recorded provenance and renders the resolution", () => {
    render(<Home />);
    expect(
      screen.getByText("A convincing answer is not a release decision."),
    ).toBeInTheDocument();
    expect(screen.getByText(/Slack-style simulation/)).toBeInTheDocument();
    expect(screen.getAllByText("Payments Platform").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/cluster ID is not available/i).length,
    ).toBeGreaterThan(0);
  });

  it("shows exact approval details and a synthetic-only action flow", () => {
    render(<Home />);
    expect(screen.getByText(/inert jira proposal/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText("Inspect exact approval payload"));
    expect(screen.getAllByText(/sha256:/i).length).toBeGreaterThan(0);
    fireEvent.click(
      screen.getByRole("button", { name: /simulate exact approval/i }),
    );
    expect(screen.getByText("APPROVED")).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: /run synthetic connector/i }),
    );
    expect(screen.getByText("COMPLETE")).toBeInTheDocument();
    expect(screen.getByText("SYN-1")).toBeInTheDocument();
  });
});

import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import Home from "./page";

describe("snapshot-first home", () => {
  it("labels synthetic recorded provenance and renders the resolution", () => {
    render(<Home />);
    expect(screen.getByText("Recorded fixture")).toBeInTheDocument();
    expect(screen.getByText(/Slack-style simulation/)).toBeInTheDocument();
    expect(screen.getAllByText("Payments Platform").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/cluster ID is not available/i).length,
    ).toBeGreaterThan(0);
  });
});

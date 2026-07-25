import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import Home from "./page";

describe("snapshot-first home", () => {
  it("explains the product and labels the recorded synthetic demo", () => {
    render(<Home />);
    expect(
      screen.getByText(/what if a workplace ai sounds right/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/recorded.*synthetic/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText("Payments Platform").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/cluster ID is not available/i).length,
    ).toBeGreaterThan(0);
  });

  it("shows the retained failure, guarded result, and honest limits", () => {
    render(<Home />);
    expect(screen.getAllByText("NO SHIP").length).toBeGreaterThan(0);
    expect(screen.getAllByText("SHIP WITH LIMITS").length).toBeGreaterThan(0);
    expect(screen.getByText(/0 reviewers \/ 0 cases/i)).toBeInTheDocument();
    expect(
      screen.getByText(/not a final release verdict/i),
    ).toBeInTheDocument();
  });
});

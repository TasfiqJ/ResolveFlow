import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import Home from "./page";

describe("snapshot-first home", () => {
  it("makes the product and builder contribution unmistakable", () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", {
        name: /i built the release gate ai agents are missing/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/built end-to-end by tasfiq/i)).toBeInTheDocument();
    expect(screen.getAllByText(/recorded.*synthetic/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText("Payments Platform").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/cluster ID is not available/i).length,
    ).toBeGreaterThan(0);
  });

  it("shows the replay result, engineering proof, and honest limits", () => {
    render(<Home />);
    expect(screen.getAllByText("NO SHIP").length).toBeGreaterThan(0);
    expect(screen.getAllByText("SHIP WITH LIMITS").length).toBeGreaterThan(0);
    expect(screen.getByText("134")).toBeInTheDocument();
    expect(screen.getByText(/not a prompt/i)).toBeInTheDocument();
    expect(screen.getByText(/0 reviewers \/ 0 cases/i)).toBeInTheDocument();
    expect(
      screen.getByText(/not a final release verdict/i),
    ).toBeInTheDocument();
  });
});

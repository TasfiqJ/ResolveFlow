import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import CoherePage from "./page";

describe("Cohere integration receipt", () => {
  it("shows the recorded model stack, control boundary, and failure-safe outcome", () => {
    render(<CoherePage />);

    expect(
      screen.getByRole("heading", {
        name: /cohere is the engine\. ordinary code is the safety boundary/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/embed-v4\.0 supplied/i)).toBeInTheDocument();
    expect(screen.getByText(/rerank-v4\.0-fast reranked/i)).toBeInTheDocument();
    expect(screen.getByText(/command-a-plus-05-2026/i)).toBeInTheDocument();
    expect(screen.getByText("tool_authorization_denied")).toBeInTheDocument();
    expect(screen.getAllByText(/needs review/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/zero external writes/i).length).toBeGreaterThan(
      0,
    );
  });

  it("publishes valid authorization evidence without relabeling void quality", () => {
    render(<CoherePage />);

    expect(screen.getByText("32")).toBeInTheDocument();
    expect(screen.getByText("16/16")).toBeInTheDocument();
    expect(screen.getByText("0/16")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: /no model-quality victory is claimed/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /one invocation in/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/excludes 63 older snapshots/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/unavailable rather than reported as zero/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/no post-change live result/i)).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: /six Cohere contract boundaries, verified offline/i,
      }),
    ).toBeInTheDocument();
  });

  it("links directly to raw artifacts and official Cohere documentation", () => {
    render(<CoherePage />);

    expect(
      screen.getByRole("link", { name: /raw live snapshot/i }),
    ).toHaveAttribute("href", "/snapshots/hero-cohere-live.json");
    expect(
      screen.getByRole("link", { name: /raw a\/b projection/i }),
    ).toHaveAttribute("href", "/snapshots/ab-site-current.json");
    expect(
      screen.getByRole("link", { name: /command a\+ docs/i }),
    ).toHaveAttribute("href", "https://docs.cohere.com/docs/command-a-plus");
  });
});

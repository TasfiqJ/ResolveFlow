import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import ab from "../../../public/snapshots/ab-site-current.json";
import AbResultsPage from "./page";

describe("live A/B evidence page", () => {
  it("derives provenance and validity from the retained snapshot", () => {
    render(<AbResultsPage />);

    expect(
      screen.getByRole("heading", {
        name: new RegExp(`live Cohere.*${ab.run_count} runs`, "i"),
      }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/16 unsafe-v0 \+ 16 guarded-v1/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(
        /forbidden evidence reached retrieval in 16\/16 unsafe/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getAllByText("VOID").length).toBeGreaterThan(0);
    expect(
      screen.queryByText(/no live Cohere run has been performed/i),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/b1, b1/)).not.toBeInTheDocument();
    expect(screen.getAllByText("b1, b2").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /one coherent invocation/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/63 snapshots from other invocation/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/233 calls: 27/i)).toBeInTheDocument();
    expect(
      screen.getByText(/usage is unavailable, not zero/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/execution git state/i)).toBeInTheDocument();
  });

  it("links to the exported checksummed artifacts", () => {
    render(<AbResultsPage />);

    expect(
      screen.getByRole("link", { name: "ab-site-current.json" }),
    ).toHaveAttribute("href", "/snapshots/ab-site-current.json");
    expect(screen.getByRole("link", { name: "SHA-256" })).toHaveAttribute(
      "href",
      "/snapshots/ab-site-current.json.sha256",
    );
  });
});

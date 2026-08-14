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
    expect(screen.queryByText("SHIP WITH LIMITS")).not.toBeInTheDocument();
    expect(screen.getByText("5/5")).toBeInTheDocument();
    expect(screen.getByText("200/200")).toBeInTheDocument();
    expect(screen.getByText(/0 open issues/i)).toBeInTheDocument();
    expect(screen.getByText(/not a prompt/i)).toBeInTheDocument();
    expect(screen.getByText(/0 reviewers \/ 0 cases/i)).toBeInTheDocument();
    expect(
      screen.getByText(/final production release verdict/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/public by design\. local by proof/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/static, credential-free evidence viewer/i),
    ).toBeInTheDocument();
    expect(screen.getByText("149")).toBeInTheDocument();
    expect(screen.getByText("24")).toBeInTheDocument();
    expect(screen.getByText(/fde-style systems exercise/i)).toBeInTheDocument();
    expect(
      screen.getByText(/from an operator's problem to a release decision/i),
    ).toBeInTheDocument();
  });

  it("publishes deep-linkable demo and structured-output evidence", () => {
    const { container } = render(<Home />);

    expect(container.querySelector("#side-by-side")).toBeInTheDocument();
    expect(
      container.querySelector("#structured-output-stress"),
    ).toBeInTheDocument();
    expect(screen.getByText("ADMITTED TO RETRIEVAL")).toBeInTheDocument();
    expect(screen.getByText("REFUSED BEFORE RETRIEVAL")).toBeInTheDocument();
    expect(screen.getByText(/earlier a\/b run — voided/i)).toBeInTheDocument();
    expect(screen.getAllByText("unmeasured").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("link", { name: /raw retained calls/i }),
    ).toHaveAttribute("href", "results/structured-output-stress.json");
  });

  it("publishes the completion-budget result without claiming a live fix", () => {
    const { container } = render(<Home />);

    expect(container.querySelector("#completion-budget")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: /did not fix guarded live completion/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/not a controlled rate comparison/i),
    ).toHaveLength(2);
    expect(
      screen.getByRole("link", { name: /full study \+ run table/i }),
    ).toHaveAttribute(
      "href",
      "results/completion-budget-study/completion-budget-study.json",
    );
  });
});

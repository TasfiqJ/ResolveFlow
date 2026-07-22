"use client";

import { useMemo, useState } from "react";

export function ReviewForm() {
  const [submitted, setSubmitted] = useState(false);
  const order = useMemo(() => {
    let value = 0;
    for (const char of "review-fixture-001")
      value = (value * 31 + char.charCodeAt(0)) >>> 0;
    return value % 2 ? ["A", "B"] : ["B", "A"];
  }, []);
  return submitted ? (
    <div className="fallbackNotice" role="status">
      Response prepared for private export. No reviewer result was published.
    </div>
  ) : (
    <form
      className="reviewForm"
      onSubmit={(event) => {
        event.preventDefault();
        setSubmitted(true);
      }}
    >
      <fieldset>
        <legend>Compare blinded outputs {order.join(" / ")}</legend>
        <div className="comparisonGrid">
          <article className="buildCard">
            <small>OUTPUT A</small>
            <h2>Route to Payments Platform</h2>
            <p>
              Identify the affected cluster before rollback and compare the
              post-rollout error rate.
            </p>
          </article>
          <article className="buildCard">
            <small>OUTPUT B</small>
            <h2>Investigate the rollout</h2>
            <p>
              Escalate immediately and create a ticket based on all available
              sources.
            </p>
          </article>
        </div>
      </fieldset>
      <label>
        Routing usefulness{" "}
        <input required type="range" min="1" max="5" defaultValue="3" />
      </label>
      <label>
        Evidence sufficiency{" "}
        <input required type="range" min="1" max="5" defaultValue="3" />
      </label>
      <label>
        Action safety{" "}
        <input required type="range" min="1" max="5" defaultValue="3" />
      </label>
      <label>
        Clarity <input required type="range" min="1" max="5" defaultValue="3" />
      </label>
      <label>
        Decision{" "}
        <select required defaultValue="">
          <option value="" disabled>
            Select…
          </option>
          <option>accept</option>
          <option>minor_edit</option>
          <option>major_edit</option>
          <option>reject</option>
        </select>
      </label>
      <label>
        Reviewer role{" "}
        <select required defaultValue="">
          <option value="" disabled>
            Select…
          </option>
          <option>incident responder</option>
          <option>support engineer</option>
          <option>AI platform engineer</option>
          <option>security reviewer</option>
        </select>
      </label>
      <label>
        Optional rationale <textarea rows={4} />
      </label>
      <button type="submit">Prepare private response</button>
    </form>
  );
}

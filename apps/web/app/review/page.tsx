import { ReviewForm } from "./review-form";

export default function ReviewPage() {
  return (
    <main className="pageShell" id="main-content">
      <header className="pageIntro">
        <p className="eyebrow">PRIVATE REVIEW WORKFLOW</p>
        <h1>Blinded practitioner review.</h1>
        <p>
          Build and model identities are hidden. The gold route remains hidden
          until submission. This static workflow stores nothing remotely and
          publishes no invented response.
        </p>
      </header>
      <ReviewForm />
    </main>
  );
}

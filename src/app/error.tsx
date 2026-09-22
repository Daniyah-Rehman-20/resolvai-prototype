"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <div className="error-box">
      <h1>Something went wrong</h1>
      <p>The page could not load. Try again to return to your workspace.</p>
      <button className="button" onClick={reset}>
        Try again
      </button>
    </div>
  );
}

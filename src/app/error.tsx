"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <main className="page-state">
      <h1>Something went wrong</h1>
      <p>The page could not load. Try again to return to your support space.</p>
      <button className="button" onClick={reset}>
        Try again
      </button>
    </main>
  );
}

import Link from "next/link";

export default function NotFound() {
  return (
    <main className="page-state">
      <h1>Page not found</h1>
      <p>Return to your support space to continue a conversation or review your queries.</p>
      <Link className="button" href="/support">Back to support</Link>
    </main>
  );
}

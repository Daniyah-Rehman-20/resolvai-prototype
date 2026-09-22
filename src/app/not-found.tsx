import Link from "next/link";
export default function NotFound() {
  return (
    <div className="empty">
      <h1>Page not found</h1>
      <p>Choose a page from the sidebar or return to the dashboard.</p>
      <Link className="button" href="/dashboard">
        Back to dashboard
      </Link>
    </div>
  );
}

export default function HomePage() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-12">
      <section
        aria-labelledby="page-title"
        className="w-full max-w-xl rounded-xl border border-slate-200 bg-white p-6 sm:p-10"
      >
        <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
          Demo environment
        </p>

        <h1
          id="page-title"
          className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl"
        >
          PayResolve AI
        </h1>

        <p className="mt-4 leading-7 text-slate-600">
          A workspace for investigating payment issues and reviewing
          AI recommendations with human approval.
        </p>

        <p className="mt-6 rounded-lg bg-slate-100 p-4 text-sm text-slate-700">
          Step 1 is ready. All payment operations in this demo will be simulated.
        </p>
      </section>
    </main>
  );
}

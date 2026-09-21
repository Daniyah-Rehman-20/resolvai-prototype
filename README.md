# PayResolve AI

Agentic Payment Investigation & Resolution System — frontend learning project by Daniyah Rehman.

## Current milestone: Step 1

This commit initializes Next.js App Router, React, TypeScript, Tailwind CSS, and ESLint. It provides a responsive starter page and folders for later milestones. Payment investigations, approvals, integrations, and financial operations are not implemented yet. All future demo payment operations will be simulations.

## Run locally

Install a supported Node.js LTS release (minimum 20.9) and npm, then:

```bash
git clone https://github.com/Daniyah-Rehman-20/resolvai-prototype.git
cd resolvai-prototype
npm ci
npm run dev
```

Open http://localhost:3000 or the alternate address printed by the terminal. Keep the terminal running; press Ctrl+C to stop it.

You should see a centered white panel with “Demo environment,” “PayResolve AI,” a project description, and a Step 1 readiness message on a pale background.

## Check the code

```bash
npm run lint
npm run typecheck
npm run build
```

To serve the production build after `npm run build`, run `npm start`.

## Architecture

| Path | Responsibility |
| --- | --- |
| `src/app/layout.tsx` | Required HTML wrapper, shared stylesheet, and page metadata. |
| `src/app/page.tsx` | Starter page at `/`. |
| `src/app/globals.css` | Tailwind import and baseline styles. |
| `src/components/` | Future reusable layout and feature components. |
| `src/lib/types/` | Future domain types for transactions, investigations, and approvals. |
| `src/lib/mocks/` | Future fictional demo data. |
| `src/lib/api/` | Future service functions, initially backed by mocks and later FastAPI. |
| `src/lib/utils/` | Future shared formatting and other helpers. |
| `public/` | Future static assets. |

The empty folders contain `.gitkeep` placeholders so Git preserves them. Future routes will live under `src/app/`, including `dashboard`, `transactions`, `transactions/[id]`, `investigator`, `approvals`, `disputes`, `knowledge`, `agents`, `analytics`, and `settings`.

Keep UI components dependent on service functions rather than importing mock data directly. The service implementation can then change when FastAPI is available.

## Understanding the starter files

- React components are functions that return JSX, the HTML-like markup in `.tsx` files.
- Next.js maps `src/app/page.tsx` to `/` and wraps it in the root layout.
- `children: ReactNode` describes the page content inserted into that layout.
- TypeScript checks types during development; `strict` mode is enabled.
- The `@/*` import alias maps to `src/*`.
- Tailwind classes express spacing, colors, and sizing. `p-6 sm:p-10` increases padding on larger screens.
- The starter page is static and needs no client-side state or `use client` directive.
- System fonts keep the starter independent of external font downloads.

Next.js provides shared layouts and file-based routing for the planned dashboard. TypeScript supports consistent payment data models. shadcn/ui, Lucide, and charts can be added when a milestone needs them.

## Manual checks

1. Confirm the page renders and the browser tab says “PayResolve AI.”
2. Edit the heading in `src/app/page.tsx`, save, and confirm it updates in the browser.
3. Narrow the browser to a phone-sized window and check that there is no horizontal scrolling.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `node` or `npm` is not recognized | Install Node.js and reopen the terminal. |
| PowerShell blocks `npm.ps1` | Use Command Prompt from the VS Code terminal dropdown. |
| `package.json` cannot be found | Change into `resolvai-prototype` first. |
| Port 3000 is occupied | Use the alternate URL printed by Next.js. |
| Styles are missing | Check the stylesheet import in `layout.tsx` and the Tailwind import in `globals.css`. |

## Small exercise

Add “Built by Daniyah Rehman” below the description using `text-sm text-slate-500`.

## Next milestone

After confirming Step 1 works, build the shared sidebar and top navigation in Step 2.
"# resolvai-prototype" 

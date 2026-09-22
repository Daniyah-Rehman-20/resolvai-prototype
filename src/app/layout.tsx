import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Workspace } from "@/components/layout/workspace";
import "./globals.css";
export const metadata: Metadata = {
  title: "PayResolve AI | Payment Operations",
  description:
    "Investigate payment issues, review evidence, and authorize simulated resolutions.",
};
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Workspace>{children}</Workspace>
      </body>
    </html>
  );
}

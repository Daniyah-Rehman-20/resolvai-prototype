"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { Workspace } from "./workspace";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  if (pathname === "/support" || pathname.startsWith("/support/")) return children;
  return <Workspace>{children}</Workspace>;
}

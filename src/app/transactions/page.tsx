import { Transactions } from "@/components/transactions/transactions";
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q } = await searchParams;
  return <Transactions key={q || ""} initialQuery={q} />;
}

import { Investigator } from "@/components/investigator/investigator";
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ transaction?: string }>;
}) {
  const { transaction } = await searchParams;
  return <Investigator key={transaction || ""} transaction={transaction} />;
}

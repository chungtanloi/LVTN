import { Workspace } from "@/components/workspace";

export default function Page() {
  const configured = Boolean(
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY &&
    process.env.NEXT_PUBLIC_CONVEX_URL,
  );
  const demo =
    process.env.NODE_ENV !== "production" &&
    process.env.CPA2_DEMO_MODE === "true";
  return <Workspace connected={configured} demo={demo} />;
}

"use client";
import { ClerkProvider, useAuth } from "@clerk/nextjs";
import { ConvexProviderWithClerk } from "convex/react-clerk";
import { ConvexReactClient } from "convex/react";
import { useState } from "react";

function Connected({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () => new ConvexReactClient(process.env.NEXT_PUBLIC_CONVEX_URL!),
  );
  return (
    <ConvexProviderWithClerk client={client} useAuth={useAuth}>
      {children}
    </ConvexProviderWithClerk>
  );
}

export function Providers({
  configured,
  children,
}: {
  configured: boolean;
  children: React.ReactNode;
}) {
  if (!configured) return children;
  return (
    <ClerkProvider>
      <Connected>{children}</Connected>
    </ClerkProvider>
  );
}

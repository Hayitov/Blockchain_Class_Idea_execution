import { Loader2 } from "lucide-react";
import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useSession } from "./useSession";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { data, isLoading, isError } = useSession();

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center text-zinc-400">
        <Loader2 className="h-5 w-5 animate-spin" />
      </div>
    );
  }

  if (isError || !data) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

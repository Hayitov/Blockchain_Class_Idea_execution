import { useQueryClient } from "@tanstack/react-query";
import { Loader2, LogIn, ShieldCheck, Wallet } from "lucide-react";
import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAccount, useChainId, useConnect, useDisconnect, useSignMessage } from "wagmi";

import { api, type Me, type Nonce } from "../api";
import { buildSiweMessage } from "../auth/buildSiweMessage";
import { useSession } from "../auth/useSession";

export function SignInPage() {
  const { data: me, isLoading } = useSession();
  const { address, isConnected } = useAccount();
  const chainId = useChainId();
  const { connectors, connect, status: connectStatus } = useConnect();
  const { disconnect } = useDisconnect();
  const { signMessageAsync } = useSignMessage();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Already signed in -> bounce to /me. Hooks must run before this redirect.
  useEffect(() => {
    if (me) navigate("/me", { replace: true });
  }, [me, navigate]);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center text-zinc-400">
        <Loader2 className="h-5 w-5 animate-spin" />
      </div>
    );
  }
  if (me) return <Navigate to="/me" replace />;

  async function handleSignIn() {
    if (!address) return;
    setBusy(true);
    setError(null);
    try {
      const { nonce } = await api.post<Nonce>("/api/auth/nonce", { address });
      const message = buildSiweMessage({
        domain: window.location.host,
        address,
        uri: window.location.origin,
        chainId,
        nonce,
      });
      const signature = await signMessageAsync({ message });
      await api.post<Me>("/api/auth/verify", { message, signature });
      await queryClient.invalidateQueries({ queryKey: ["me"] });
      navigate("/me", { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center px-4 py-10">
      <div className="w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-900 p-8 shadow-xl">
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-lg bg-blue-500/10 p-2 text-blue-400">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-zinc-100">CS423 — Sign in</h1>
            <p className="text-xs text-zinc-500">Blockchain Technologies · NUU</p>
          </div>
        </div>

        <p className="mb-6 text-sm text-zinc-400">
          Connect your wallet, sign a one-time message, and you're in. Your grades are private to
          you.
        </p>

        {!isConnected ? (
          <div className="flex flex-col gap-2">
            {connectors.map((c) => (
              <button
                key={c.uid}
                type="button"
                disabled={connectStatus === "pending"}
                onClick={() => connect({ connector: c })}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-500 px-4 py-3 text-sm font-medium text-white transition hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <Wallet className="h-4 w-4" />
                Connect {c.name}
              </button>
            ))}
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <p className="break-all rounded-lg bg-zinc-950 px-3 py-2 font-mono text-xs text-zinc-300">
              {address}
            </p>
            <button
              type="button"
              disabled={busy}
              onClick={handleSignIn}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-500 px-4 py-3 text-sm font-medium text-white transition hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <LogIn className="h-4 w-4" />}
              {busy ? "Signing…" : "Sign in with Ethereum"}
            </button>
            <button
              type="button"
              onClick={() => disconnect()}
              className="rounded-lg border border-zinc-800 px-4 py-2 text-xs text-zinc-400 transition hover:bg-zinc-800"
            >
              Disconnect
            </button>
          </div>
        )}

        {error ? (
          <p className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
            {error}
          </p>
        ) : null}
      </div>
    </div>
  );
}

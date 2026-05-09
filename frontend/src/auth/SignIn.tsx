import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useAccount, useChainId, useConnect, useDisconnect, useSignMessage } from "wagmi";

import { api, type Me, type Nonce } from "../api";
import styles from "../styles/App.module.css";
import { buildSiweMessage } from "./buildSiweMessage";

export function SignIn() {
  const { address, isConnected } = useAccount();
  const chainId = useChainId();
  const { connectors, connect, status: connectStatus } = useConnect();
  const { disconnect } = useDisconnect();
  const { signMessageAsync } = useSignMessage();
  const queryClient = useQueryClient();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={styles.signInCard}>
      <h1>CS423 — Sign in</h1>
      <p className={styles.subtitle}>
        Connect your wallet, sign a one-time message, and you're in. Your grades
        are private to you.
      </p>

      {!isConnected ? (
        <div className={styles.connectorList}>
          {connectors.map((c) => (
            <button
              key={c.uid}
              type="button"
              className={styles.primaryButton}
              disabled={connectStatus === "pending"}
              onClick={() => connect({ connector: c })}
            >
              Connect {c.name}
            </button>
          ))}
        </div>
      ) : (
        <>
          <p className={styles.address}>{address}</p>
          <button
            type="button"
            className={styles.primaryButton}
            disabled={busy}
            onClick={handleSignIn}
          >
            {busy ? "Signing..." : "Sign in with Ethereum"}
          </button>
          <button type="button" className={styles.secondaryButton} onClick={() => disconnect()}>
            Disconnect
          </button>
        </>
      )}

      {error ? <p className={styles.error}>{error}</p> : null}
    </div>
  );
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BookOpen,
  CheckCircle2,
  Clock,
  Loader2,
  LogOut,
  Send,
  XCircle,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { api, type Assignment, type GraderRun, type Submission } from "../api";
import { useSession } from "../auth/useSession";

export function ProfilePage() {
  const { data: me } = useSession();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const assignmentsQuery = useQuery({
    queryKey: ["assignments"],
    queryFn: () => api.get<Assignment[]>("/api/assignments"),
    enabled: !!me?.student,
  });

  const submissionsQuery = useQuery({
    queryKey: ["submissions"],
    queryFn: () => api.get<Submission[]>("/api/me/submissions"),
    enabled: !!me?.student,
  });

  const submitMutation = useMutation({
    mutationFn: (code: string) => api.post<GraderRun>(`/api/assignments/${code}/submit`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["submissions"] }),
  });

  if (!me) return null;

  async function handleLogout() {
    await api.post("/api/auth/logout");
    await queryClient.invalidateQueries({ queryKey: ["me"] });
    navigate("/", { replace: true });
  }

  return (
    <div className="mx-auto flex min-h-full max-w-3xl flex-col gap-6 px-4 py-8">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{me.student?.name ?? "Welcome"}</h1>
          <p className="mt-1 break-all font-mono text-xs text-zinc-500">{me.address}</p>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          className="inline-flex items-center gap-2 rounded-lg border border-zinc-800 px-3 py-2 text-xs text-zinc-400 transition hover:bg-zinc-800"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </header>

      {!me.student ? (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-200">
          Wallet authenticated, but no student record is linked to this address. Contact the
          course staff to be added to the gradebook.
        </div>
      ) : (
        <>
          <section className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
            <div className="mb-4 flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-zinc-400" />
              <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-300">
                Assignments
              </h2>
            </div>

            {assignmentsQuery.isLoading ? (
              <p className="text-sm text-zinc-500">Loading…</p>
            ) : null}

            <div className="divide-y divide-zinc-800">
              {assignmentsQuery.data?.map((a) => {
                const latest = submissionsQuery.data
                  ?.filter((s) => s.assignment_code === a.code)
                  .at(0);
                const latestRun = latest?.runs.at(0);
                const isRunningHere =
                  submitMutation.isPending && submitMutation.variables === a.code;
                return (
                  <div
                    key={a.id}
                    className="flex items-center justify-between gap-4 py-4 first:pt-0 last:pb-0"
                  >
                    <div>
                      <div className="font-medium">{a.title}</div>
                      <div className="mt-1 flex items-center gap-2 text-xs text-zinc-500">
                        <span>weight {a.weight}</span>
                        {latestRun ? (
                          <>
                            <span>·</span>
                            <span>
                              last score{" "}
                              <span className="font-semibold text-zinc-200">
                                {latestRun.score ?? "—"}
                              </span>
                            </span>
                            <span>·</span>
                            <RunStatusBadge status={latestRun.status} />
                          </>
                        ) : null}
                      </div>
                    </div>
                    <button
                      type="button"
                      disabled={isRunningHere}
                      onClick={() => submitMutation.mutate(a.code)}
                      className="inline-flex items-center gap-2 rounded-lg bg-blue-500 px-3 py-2 text-sm font-medium text-white transition hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {isRunningHere ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Send className="h-4 w-4" />
                      )}
                      {isRunningHere ? "Running…" : "Submit"}
                    </button>
                  </div>
                );
              })}
            </div>

            {submitMutation.isError ? (
              <p className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
                {submitMutation.error?.message}
              </p>
            ) : null}
          </section>

          <section className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
            <div className="mb-4 flex items-center gap-2">
              <Clock className="h-4 w-4 text-zinc-400" />
              <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-300">
                Submission history
              </h2>
            </div>

            {submissionsQuery.isLoading ? (
              <p className="text-sm text-zinc-500">Loading…</p>
            ) : null}
            {submissionsQuery.data && submissionsQuery.data.length === 0 ? (
              <p className="text-sm text-zinc-500">No submissions yet.</p>
            ) : null}

            <div className="divide-y divide-zinc-800">
              {submissionsQuery.data?.map((s) => {
                const run = s.runs.at(0);
                return (
                  <div
                    key={s.id}
                    className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0"
                  >
                    <div>
                      <div className="text-sm font-medium">{s.assignment_code}</div>
                      <div className="text-xs text-zinc-500">
                        {new Date(s.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <RunStatusBadge status={run?.status ?? "no run"} />
                      <div className="text-right">
                        <div className="text-lg font-semibold">{run?.score ?? "—"}</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function RunStatusBadge({ status }: { status: string }) {
  if (status === "ok") {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-emerald-400">
        <CheckCircle2 className="h-3.5 w-3.5" />
        ok
      </span>
    );
  }
  if (status === "error") {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-red-400">
        <XCircle className="h-3.5 w-3.5" />
        error
      </span>
    );
  }
  return <span className="text-xs text-zinc-500">{status}</span>;
}

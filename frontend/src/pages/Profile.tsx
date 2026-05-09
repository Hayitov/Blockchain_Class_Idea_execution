import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type Assignment, type GraderRun, type Submission } from "../api";
import { useSession } from "../auth/useSession";
import styles from "../styles/Profile.module.css";

export function Profile() {
  const { data: me } = useSession();
  const queryClient = useQueryClient();

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
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1>{me.student?.name ?? "Welcome"}</h1>
          <p className={styles.address}>{me.address}</p>
        </div>
        <button type="button" className={styles.secondaryButton} onClick={handleLogout}>
          Sign out
        </button>
      </header>

      {!me.student ? (
        <div className={styles.notice}>
          Wallet authenticated, but no student record is linked to this address yet.
          Contact the course staff to be added to the gradebook.
        </div>
      ) : (
        <>
          <section className={styles.assignmentList}>
            <h2>Assignments</h2>
            {assignmentsQuery.isLoading ? <p className={styles.placeholder}>Loading…</p> : null}
            {assignmentsQuery.data?.map((a) => {
              const latest = submissionsQuery.data
                ?.filter((s) => s.assignment_code === a.code)
                .at(0);
              const latestRun = latest?.runs.at(0);
              return (
                <div key={a.id} className={styles.assignmentRow}>
                  <div>
                    <div className={styles.assignmentTitle}>{a.title}</div>
                    <div className={styles.placeholder}>
                      weight {a.weight}
                      {latestRun ? (
                        <>
                          {" · last score: "}
                          <strong>{latestRun.score ?? "—"}</strong>{" · "}
                          <span>{latestRun.status}</span>
                        </>
                      ) : null}
                    </div>
                  </div>
                  <button
                    type="button"
                    className={styles.primaryButton}
                    disabled={submitMutation.isPending}
                    onClick={() => submitMutation.mutate(a.code)}
                  >
                    {submitMutation.isPending && submitMutation.variables === a.code
                      ? "Running…"
                      : "Submit"}
                  </button>
                </div>
              );
            })}
            {submitMutation.isError ? (
              <p className={styles.error}>{submitMutation.error?.message}</p>
            ) : null}
          </section>

          <section className={styles.assignmentList}>
            <h2>Submission history</h2>
            {submissionsQuery.isLoading ? <p className={styles.placeholder}>Loading…</p> : null}
            {submissionsQuery.data?.length === 0 ? (
              <p className={styles.placeholder}>No submissions yet.</p>
            ) : null}
            {submissionsQuery.data?.map((s) => {
              const run = s.runs.at(0);
              return (
                <div key={s.id} className={styles.historyRow}>
                  <div>
                    <strong>{s.assignment_code}</strong>
                    <div className={styles.placeholder}>
                      {new Date(s.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div className={styles.historyScore}>
                    <div>{run?.score ?? "—"}</div>
                    <div className={styles.placeholder}>{run?.status ?? "no run"}</div>
                  </div>
                </div>
              );
            })}
          </section>
        </>
      )}
    </div>
  );
}

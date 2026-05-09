import { useQueryClient } from "@tanstack/react-query";

import { api } from "../api";
import { useSession } from "../auth/useSession";
import styles from "../styles/Profile.module.css";

export function Profile() {
  const { data } = useSession();
  const queryClient = useQueryClient();

  if (!data) return null;

  async function handleLogout() {
    await api.post("/api/auth/logout");
    await queryClient.invalidateQueries({ queryKey: ["me"] });
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1>{data.student?.name ?? "Welcome"}</h1>
          <p className={styles.address}>{data.address}</p>
        </div>
        <button type="button" className={styles.secondaryButton} onClick={handleLogout}>
          Sign out
        </button>
      </header>

      {!data.student ? (
        <div className={styles.notice}>
          Wallet authenticated, but no student record is linked to this address yet.
          Contact the course staff to be added to the gradebook.
        </div>
      ) : (
        <section className={styles.assignmentList}>
          <h2>Assignments</h2>
          <p className={styles.placeholder}>
            Assignment list and submission UI are wired in the next step.
          </p>
        </section>
      )}
    </div>
  );
}

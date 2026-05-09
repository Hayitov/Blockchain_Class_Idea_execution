import { SignIn } from "./auth/SignIn";
import { useSession } from "./auth/useSession";
import { Profile } from "./pages/Profile";
import styles from "./styles/App.module.css";

export function App() {
  const { data, isLoading } = useSession();

  if (isLoading) {
    return <div className={styles.appShell}>Loading…</div>;
  }

  return <div className={styles.appShell}>{data ? <Profile /> : <SignIn />}</div>;
}

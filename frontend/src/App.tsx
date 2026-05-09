import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "./auth/ProtectedRoute";
import { SignInPage } from "./pages/SignInPage";
import { ProfilePage } from "./pages/ProfilePage";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<SignInPage />} />
      <Route
        path="/me"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

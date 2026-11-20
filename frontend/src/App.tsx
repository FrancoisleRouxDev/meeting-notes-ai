import { Navigate, Route, Routes } from "react-router-dom";
import RequireAuth from "./components/RequireAuth";
import AuthPage from "./pages/AuthPage";
import MeetingsPage from "./pages/MeetingsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/register" element={<AuthPage mode="register" />} />
      <Route element={<RequireAuth />}>
        <Route path="/meetings" element={<MeetingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/meetings" replace />} />
    </Routes>
  );
}
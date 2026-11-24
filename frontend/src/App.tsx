import { Navigate, Route, Routes } from "react-router-dom";
import RequireAuth from "./components/RequireAuth";
import Layout from "./components/Layout";
import AuthPage from "./pages/AuthPage";
import MeetingDetailPage from "./pages/MeetingDetailPage";
import MeetingsPage from "./pages/MeetingsPage";
import NewMeetingPage from "./pages/NewMeetingPage";
import OpenItemsPage from "./pages/OpenItemsPage";
import AccountPage from "./pages/AccountPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/register" element={<AuthPage mode="register" />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />}></Route>
      <Route path="/reset-password" element={<ResetPasswordPage />}></Route>
      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route path="/meetings" element={<MeetingsPage />} />
          <Route path="/meetings/new" element={<NewMeetingPage />} />
          <Route path="/meetings/:id" element={<MeetingDetailPage />} />
          <Route path="/items" element={<OpenItemsPage />} />
          <Route path="/account" element={<AccountPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/meetings" replace />} />
    </Routes>
  );
}
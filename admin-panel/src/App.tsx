import { Suspense, lazy } from "react";
import { Spin } from "antd";
import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { AppLayout } from "./layouts/AppLayout";
import { LoginPage } from "./pages/LoginPage";

const DashboardPage = lazy(() => import("./pages/DashboardPage").then((m) => ({ default: m.DashboardPage })));
const TicketsPage = lazy(() => import("./pages/TicketsPage").then((m) => ({ default: m.TicketsPage })));
const UsersPage = lazy(() => import("./pages/UsersPage").then((m) => ({ default: m.UsersPage })));
const EndUsersPage = lazy(() => import("./pages/EndUsersPage").then((m) => ({ default: m.EndUsersPage })));
const FacultiesPage = lazy(() => import("./pages/FacultiesPage").then((m) => ({ default: m.FacultiesPage })));
const DepartmentsPage = lazy(() =>
  import("./pages/DepartmentsPage").then((m) => ({ default: m.DepartmentsPage })),
);
const InventoryPage = lazy(() => import("./pages/InventoryPage").then((m) => ({ default: m.InventoryPage })));

function PageFallback() {
  return (
    <div style={{ display: "flex", justifyContent: "center", padding: 48 }}>
      <Spin size="large" />
    </div>
  );
}

function App() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route index element={<Navigate to="/tickets" replace />} />
            <Route path="/tickets" element={<TicketsPage />} />
            <Route path="/inventory" element={<InventoryPage />} />

            <Route element={<ProtectedRoute allowedRoles={["super_admin"]} />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/users" element={<UsersPage />} />
              <Route path="/end-users" element={<EndUsersPage />} />
              <Route path="/faculties" element={<FacultiesPage />} />
              <Route path="/departments" element={<DepartmentsPage />} />
            </Route>
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

export default App;

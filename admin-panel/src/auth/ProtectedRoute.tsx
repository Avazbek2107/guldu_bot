import { Spin, Typography } from "antd";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { firstAccessibleRoute, hasPermission } from "./permissions";
import type { PermissionAction, PermissionResource, UserRole } from "../types";

interface ProtectedRouteProps {
  allowedRoles?: UserRole[];
  permission?: { resource: PermissionResource; action?: PermissionAction };
}

export function ProtectedRoute({ allowedRoles, permission }: ProtectedRouteProps) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
        <Spin size="large" />
      </div>
    );
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles || permission) {
    const roleAllowed = allowedRoles?.includes(user.role) ?? false;
    const permissionAllowed = permission ? hasPermission(user, permission.resource, permission.action) : false;
    if (!roleAllowed && !permissionAllowed) {
      const fallback = firstAccessibleRoute(user);
      if (fallback && fallback !== location.pathname) {
        return <Navigate to={fallback} replace />;
      }
      // No page at all is accessible to this account (or the fallback itself
      // just failed) — stop redirecting so we don't loop forever between
      // gated routes; show a terminal message instead.
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 8,
            justifyContent: "center",
            alignItems: "center",
            height: "100vh",
            textAlign: "center",
            padding: 24,
          }}
        >
          <Typography.Title level={4}>Ruxsat yo'q</Typography.Title>
          <Typography.Text type="secondary">
            Hisobingizga hech qanday sahifani ko'rish huquqi berilmagan. Administrator bilan bog'laning.
          </Typography.Text>
        </div>
      );
    }
  }

  return <Outlet />;
}

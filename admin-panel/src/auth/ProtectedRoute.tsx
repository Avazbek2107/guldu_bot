import { Spin } from "antd";
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { hasPermission } from "./permissions";
import type { PermissionAction, PermissionResource, UserRole } from "../types";

interface ProtectedRouteProps {
  allowedRoles?: UserRole[];
  permission?: { resource: PermissionResource; action?: PermissionAction };
}

export function ProtectedRoute({ allowedRoles, permission }: ProtectedRouteProps) {
  const { user, loading } = useAuth();

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
      return <Navigate to="/tickets" replace />;
    }
  }

  return <Outlet />;
}

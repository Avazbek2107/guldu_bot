import type { PermissionAction, PermissionResource, UserOut } from "../types";

export function hasPermission(
  user: UserOut | null,
  resource: PermissionResource,
  action: PermissionAction = "view",
): boolean {
  if (!user) return false;
  if (user.role === "super_admin") return true;
  if (user.role === "admin") {
    return Boolean(user.permissions?.[resource]?.includes(action));
  }
  return false;
}

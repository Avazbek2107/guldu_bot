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

/** First route (in sidebar order) this user is actually allowed to reach, or null if none. */
export function firstAccessibleRoute(user: UserOut | null): string | null {
  if (!user) return null;
  const isTechnician = user.role === "technician_main" || user.role === "technician_backup";
  if (hasPermission(user, "dashboard")) return "/dashboard";
  if (isTechnician || hasPermission(user, "tickets")) return "/tickets";
  if (isTechnician || hasPermission(user, "inventory")) return "/inventory";
  if (hasPermission(user, "users")) return "/users";
  if (hasPermission(user, "end_users")) return "/end-users";
  if (hasPermission(user, "faculties")) return "/faculties";
  if (hasPermission(user, "departments")) return "/departments";
  return null;
}

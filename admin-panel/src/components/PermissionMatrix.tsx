import { Checkbox } from "antd";
import {
  PERMISSION_ACTION_LABELS_UZ,
  PERMISSION_RESOURCE_LABELS_UZ,
  type PermissionAction,
  type PermissionResource,
} from "../types";

const RESOURCE_ORDER: PermissionResource[] = [
  "dashboard",
  "tickets",
  "inventory",
  "users",
  "end_users",
  "faculties",
  "departments",
  "projects",
  "payments",
];
const ALL_ACTIONS: PermissionAction[] = ["view", "create", "edit", "delete"];

export type PermissionsValue = Partial<Record<PermissionResource, PermissionAction[]>>;

export function PermissionMatrix({
  value,
  onChange,
}: {
  value?: PermissionsValue;
  onChange?: (value: PermissionsValue) => void;
}) {
  const current = value ?? {};

  function toggle(resource: PermissionResource, action: PermissionAction, checked: boolean) {
    const existing = current[resource] ?? [];
    const next = checked ? [...new Set([...existing, action])] : existing.filter((a) => a !== action);
    onChange?.({ ...current, [resource]: next });
  }

  return (
    <div style={{ border: "1px solid #f0f0f0", borderRadius: 8, overflow: "hidden" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
        <thead>
          <tr style={{ background: "#fafafa" }}>
            <th style={{ textAlign: "left", padding: "8px 12px", fontWeight: 600 }}>Bo'lim</th>
            {ALL_ACTIONS.map((action) => (
              <th key={action} style={{ textAlign: "center", padding: "8px 12px", fontWeight: 600 }}>
                {PERMISSION_ACTION_LABELS_UZ[action]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {RESOURCE_ORDER.map((resource) => (
            <tr key={resource} style={{ borderTop: "1px solid #f0f0f0" }}>
              <td style={{ padding: "6px 12px" }}>{PERMISSION_RESOURCE_LABELS_UZ[resource]}</td>
              {ALL_ACTIONS.map((action) => (
                <td key={action} style={{ textAlign: "center", padding: "6px 12px" }}>
                  <Checkbox
                    checked={(current[resource] ?? []).includes(action)}
                    onChange={(e) => toggle(resource, action, e.target.checked)}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

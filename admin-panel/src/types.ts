export type UserRole = "super_admin" | "admin" | "technician_main" | "technician_backup" | "faculty_staff";

export type PermissionResource =
  | "dashboard"
  | "tickets"
  | "inventory"
  | "users"
  | "end_users"
  | "faculties"
  | "departments";

export type PermissionAction = "view" | "create" | "edit" | "delete";

export type TicketCategory =
  | "computer"
  | "network"
  | "projector"
  | "power"
  | "printer"
  | "software"
  | "other";

export type TicketPriority = "urgent" | "normal";

export type TicketStatus = "open" | "in_progress" | "closed";

export const CATEGORY_LABELS_UZ: Record<TicketCategory, string> = {
  computer: "Kompyuter",
  network: "Tarmoq/internet",
  projector: "Proyektor",
  power: "Elektr ta'minoti",
  printer: "Printer",
  software: "Dasturiy ta'minot",
  other: "Boshqa",
};

export const PRIORITY_LABELS_UZ: Record<TicketPriority, string> = {
  urgent: "Shoshilinch",
  normal: "Oddiy",
};

export const STATUS_LABELS_UZ: Record<TicketStatus, string> = {
  open: "Ochiq",
  in_progress: "Jarayonda",
  closed: "Yopilgan",
};

export const ROLE_LABELS_UZ: Record<UserRole, string> = {
  super_admin: "Super Admin",
  admin: "Admin",
  technician_main: "Asosiy texnik xodim",
  technician_backup: "Zaxira texnik xodim",
  faculty_staff: "Fakultet xodimi",
};

export const PERMISSION_RESOURCE_LABELS_UZ: Record<PermissionResource, string> = {
  dashboard: "Dashboard",
  tickets: "Arizalar",
  inventory: "Inventar",
  users: "Xodimlar",
  end_users: "Foydalanuvchilar",
  faculties: "Fakultetlar",
  departments: "Bo'limlar",
};

export const PERMISSION_ACTION_LABELS_UZ: Record<PermissionAction, string> = {
  view: "Ko'rish",
  create: "Qo'shish",
  edit: "Tahrirlash",
  delete: "O'chirish",
};

export type TechnicianRole = "technician_main" | "technician_backup";

export interface FacultyAssignment {
  faculty_id: number;
  faculty_name: string;
  role: TechnicianRole;
}

export interface UserOut {
  id: number;
  username: string | null;
  full_name: string;
  phone: string;
  role: UserRole;
  faculty_id: number | null;
  faculty_assignments: FacultyAssignment[];
  permissions: Partial<Record<PermissionResource, PermissionAction[]>> | null;
  avatar_url: string | null;
  telegram_id: number | null;
  is_blocked: boolean;
  is_suspicious: boolean;
}

export type OrgUnitType = "faculty" | "department";

export interface FacultyOut {
  id: number;
  name: string;
  unit_type: OrgUnitType;
  parent_id: number | null;
}

export function orgUnitLabel(f: FacultyOut): string {
  return f.unit_type === "department" ? `${f.name} (bo'lim)` : f.name;
}

/** antd Select `filterOption`: keeps only options whose label starts with the
 * typed text (case-insensitive), for long lists like the fakultet/bo'lim
 * picker where matching from the first letters is more useful than a
 * substring-anywhere search. */
export function filterOptionByPrefix(input: string, option?: { label?: unknown }): boolean {
  return String(option?.label ?? "")
    .toLowerCase()
    .startsWith(input.toLowerCase());
}

export interface TicketOut {
  id: number;
  ticket_number: string;
  faculty_id: number;
  faculty_name: string;
  creator_full_name: string;
  creator_phone: string;
  category: TicketCategory;
  priority: TicketPriority;
  description: string;
  status: TicketStatus;
  assigned_technician_id: number | null;
  technician_full_name: string | null;
  default_technician_name: string | null;
  resolution_comment: string | null;
  is_suspicious: boolean;
  created_at: string;
  accepted_at: string | null;
  closed_at: string | null;
  inventory_item_id: number | null;
  inventory_number: string | null;
  closing_attachment_url: string | null;
}

export interface InventoryItemOut {
  id: number;
  faculty_id: number;
  faculty_name: string;
  sub_unit: string | null;
  room: string | null;
  inventory_number: string | null;
  uzasbo: string | null;
  inventory_type: string | null;
  model: string | null;
  status: string;
  internet_connection: string | null;
  responsible_person: string | null;
  assigned_technician_id: number | null;
  assigned_technician_name: string | null;
  repair_count: number;
  last_repaired_at: string | null;
  created_at: string;
}

export interface RepairHistoryItem {
  ticket_id: number;
  ticket_number: string;
  closed_at: string | null;
  resolution_comment: string | null;
  technician_full_name: string | null;
  is_suspicious: boolean;
}

export interface InventoryImportSkip {
  row: number;
  reason: string;
}

export interface InventoryImportResult {
  created: number;
  skipped: InventoryImportSkip[];
}

export interface FacultyImportSkip {
  row: number;
  reason: string;
}

export interface FacultyImportResult {
  created: number;
  skipped: FacultyImportSkip[];
}

export interface FacultyStat {
  faculty_id: number;
  faculty_name: string;
  total: number;
  open: number;
  in_progress: number;
  closed: number;
}

export interface ReporterStat {
  user_id: number;
  full_name: string;
  phone: string;
  faculty_id: number | null;
  faculty_name: string | null;
  total_tickets: number;
  open_tickets: number;
  suspicious_tickets: number;
  last_ticket_at: string | null;
}

export interface TechnicianStat {
  technician_id: number;
  full_name: string;
  accepted: number;
  closed: number;
  open_remaining: number;
  avg_close_hours: number | null;
  efficiency_percent: number | null;
}

export interface CategoryStat {
  category: string;
  count: number;
}

export interface DailyCount {
  date: string;
  count: number;
}

export interface InventoryStatusStat {
  status: string;
  count: number;
}

export interface InventoryFacultyStat {
  faculty_id: number;
  faculty_name: string;
  total: number;
  working: number;
  broken: number;
  in_repair: number;
  decommissioned: number;
}

export interface DashboardStats {
  total_tickets: number;
  open_tickets: number;
  in_progress_tickets: number;
  closed_tickets: number;
  faculty_stats: FacultyStat[];
  department_stats: FacultyStat[];
  technician_stats: TechnicianStat[];
  reporter_stats: ReporterStat[];
  category_stats: CategoryStat[];
  suspicious_user_count: number;
  blocked_user_count: number;
  daily_trend: DailyCount[];
  total_inventory_items: number;
  inventory_status_stats: InventoryStatusStat[];
  inventory_faculty_stats: InventoryFacultyStat[];
}

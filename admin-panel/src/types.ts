export type UserRole = "super_admin" | "technician_main" | "technician_backup" | "faculty_staff";

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
  technician_main: "Asosiy texnik xodim",
  technician_backup: "Zaxira texnik xodim",
  faculty_staff: "Fakultet xodimi",
};

export interface UserOut {
  id: number;
  username: string | null;
  full_name: string;
  phone: string;
  role: UserRole;
  faculty_id: number | null;
  telegram_id: number | null;
  is_blocked: boolean;
  is_suspicious: boolean;
}

export interface FacultyOut {
  id: number;
  name: string;
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
  resolution_comment: string | null;
  is_suspicious: boolean;
  rating_stars: number | null;
  created_at: string;
  accepted_at: string | null;
  closed_at: string | null;
  sla_deadline: string | null;
}

export interface FacultyStat {
  faculty_id: number;
  faculty_name: string;
  total: number;
  open: number;
  in_progress: number;
  closed: number;
}

export interface TechnicianStat {
  technician_id: number;
  full_name: string;
  faculty_id: number | null;
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

export interface DashboardStats {
  total_tickets: number;
  open_tickets: number;
  in_progress_tickets: number;
  closed_tickets: number;
  faculty_stats: FacultyStat[];
  technician_stats: TechnicianStat[];
  category_stats: CategoryStat[];
  average_rating: number | null;
  sla_breach_count: number;
  sla_open_breach_count: number;
  suspicious_user_count: number;
  blocked_user_count: number;
  daily_trend: DailyCount[];
}

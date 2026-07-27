import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    TECHNICIAN_MAIN = "technician_main"
    TECHNICIAN_BACKUP = "technician_backup"
    FACULTY_STAFF = "faculty_staff"


class TechnicianFacultyRole(str, enum.Enum):
    TECHNICIAN_MAIN = "technician_main"
    TECHNICIAN_BACKUP = "technician_backup"


class OrgUnitType(str, enum.Enum):
    FACULTY = "faculty"
    DEPARTMENT = "department"


class TicketCategory(str, enum.Enum):
    COMPUTER = "computer"
    NETWORK = "network"
    PROJECTOR = "projector"
    POWER = "power"
    PRINTER = "printer"
    SOFTWARE = "software"
    OTHER = "other"


class TicketPriority(str, enum.Enum):
    URGENT = "urgent"
    NORMAL = "normal"


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class AttachmentType(str, enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"

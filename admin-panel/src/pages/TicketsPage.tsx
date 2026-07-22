import { useEffect, useMemo, useState } from "react";
import {
  Button,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
  message,
} from "antd";
import { FilePdfOutlined } from "@ant-design/icons";
import { downloadTicketPdf } from "../api/client";
import { closeTicket, listTickets, reassignTicket } from "../api/tickets";
import { listFaculties } from "../api/faculties";
import { listUsers } from "../api/users";
import { useAuth } from "../auth/AuthContext";
import {
  CATEGORY_LABELS_UZ,
  PRIORITY_LABELS_UZ,
  STATUS_LABELS_UZ,
  type FacultyOut,
  type TicketOut,
  type TicketStatus,
  type UserOut,
} from "../types";

const STATUS_COLORS: Record<TicketStatus, string> = {
  open: "gold",
  in_progress: "blue",
  closed: "green",
};

export function TicketsPage() {
  const { user } = useAuth();
  const isSuperAdmin = user?.role === "super_admin";

  const [tickets, setTickets] = useState<TicketOut[]>([]);
  const [faculties, setFaculties] = useState<FacultyOut[]>([]);
  const [technicians, setTechnicians] = useState<UserOut[]>([]);
  const [loading, setLoading] = useState(true);

  const [facultyFilter, setFacultyFilter] = useState<number | undefined>();
  const [statusFilter, setStatusFilter] = useState<TicketStatus | undefined>();
  const [categoryFilter, setCategoryFilter] = useState<string | undefined>();

  const [closeTarget, setCloseTarget] = useState<TicketOut | null>(null);
  const [resolutionComment, setResolutionComment] = useState("");
  const [reassignTarget, setReassignTarget] = useState<TicketOut | null>(null);
  const [reassignTechnicianId, setReassignTechnicianId] = useState<number | undefined>();
  const [actionLoading, setActionLoading] = useState(false);

  async function loadTickets() {
    setLoading(true);
    try {
      const data = await listTickets({
        faculty_id: facultyFilter,
        status: statusFilter,
        category: categoryFilter as never,
      });
      setTickets(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    listFaculties().then(setFaculties);
    listUsers({ role: "technician_main" }).then((mainTechs) =>
      listUsers({ role: "technician_backup" }).then((backupTechs) =>
        setTechnicians([...mainTechs, ...backupTechs]),
      ),
    );
  }, []);

  useEffect(() => {
    loadTickets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [facultyFilter, statusFilter, categoryFilter]);

  const technicianOptionsForFaculty = useMemo(
    () => (facultyId: number) => technicians.filter((t) => t.faculty_id === facultyId),
    [technicians],
  );

  async function handleClose() {
    if (!closeTarget) return;
    setActionLoading(true);
    try {
      await closeTicket(closeTarget.id, resolutionComment || null);
      message.success(`Ariza #${closeTarget.ticket_number} yopildi`);
      setCloseTarget(null);
      setResolutionComment("");
      loadTickets();
    } catch {
      message.error("Xatolik yuz berdi");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleReassign() {
    if (!reassignTarget || !reassignTechnicianId) return;
    setActionLoading(true);
    try {
      await reassignTicket(reassignTarget.id, reassignTechnicianId);
      message.success(`Ariza #${reassignTarget.ticket_number} qayta yo'naltirildi`);
      setReassignTarget(null);
      setReassignTechnicianId(undefined);
      loadTickets();
    } catch {
      message.error("Xatolik yuz berdi");
    } finally {
      setActionLoading(false);
    }
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }} wrap>
        {isSuperAdmin && (
          <Select
            allowClear
            placeholder="Fakultet"
            style={{ width: 180 }}
            value={facultyFilter}
            onChange={setFacultyFilter}
            options={faculties.map((f) => ({ label: f.name, value: f.id }))}
          />
        )}
        <Select
          allowClear
          placeholder="Holat"
          style={{ width: 160 }}
          value={statusFilter}
          onChange={setStatusFilter}
          options={Object.entries(STATUS_LABELS_UZ).map(([value, label]) => ({ value, label }))}
        />
        <Select
          allowClear
          placeholder="Muammo toifasi"
          style={{ width: 180 }}
          value={categoryFilter}
          onChange={setCategoryFilter}
          options={Object.entries(CATEGORY_LABELS_UZ).map(([value, label]) => ({ value, label }))}
        />
      </Space>

      <Table
        rowKey="id"
        loading={loading}
        dataSource={tickets}
        columns={[
          { title: "Ariza №", dataIndex: "ticket_number" },
          { title: "FISH", dataIndex: "creator_full_name" },
          { title: "Telefon", dataIndex: "creator_phone" },
          ...(isSuperAdmin ? [{ title: "Fakultet", dataIndex: "faculty_name" }] : []),
          {
            title: "Toifa",
            dataIndex: "category",
            render: (value: string) => CATEGORY_LABELS_UZ[value as keyof typeof CATEGORY_LABELS_UZ] ?? value,
          },
          {
            title: "Muhimlik",
            dataIndex: "priority",
            render: (value: string) => PRIORITY_LABELS_UZ[value as keyof typeof PRIORITY_LABELS_UZ] ?? value,
          },
          {
            title: "Holat",
            dataIndex: "status",
            render: (value: TicketStatus) => <Tag color={STATUS_COLORS[value]}>{STATUS_LABELS_UZ[value]}</Tag>,
          },
          { title: "Texnik xodim", dataIndex: "technician_full_name", render: (v: string | null) => v ?? "-" },
          {
            title: "Sana",
            dataIndex: "created_at",
            render: (v: string) => new Date(v).toLocaleString("uz-UZ"),
          },
          {
            title: "Baho",
            dataIndex: "rating_stars",
            render: (v: number | null) => (v != null ? "⭐".repeat(v) : "-"),
          },
          {
            title: "Amallar",
            key: "actions",
            render: (_: unknown, record: TicketOut) => (
              <Space>
                <Tooltip title="Ma'lumotnomani yuklab olish">
                  <Button
                    size="small"
                    icon={<FilePdfOutlined />}
                    onClick={() => downloadTicketPdf(record.id, `${record.ticket_number}.pdf`)}
                  />
                </Tooltip>
                {record.status !== "closed" && (
                  <>
                    <Button size="small" onClick={() => setCloseTarget(record)}>
                      Yopish
                    </Button>
                    <Button size="small" onClick={() => setReassignTarget(record)}>
                      Qayta yo'naltirish
                    </Button>
                  </>
                )}
              </Space>
            ),
          },
        ]}
      />

      <Modal
        title={`Arizani yopish — #${closeTarget?.ticket_number ?? ""}`}
        open={closeTarget !== null}
        onCancel={() => setCloseTarget(null)}
        onOk={handleClose}
        confirmLoading={actionLoading}
        okText="Yopish"
        cancelText="Bekor qilish"
      >
        <Input.TextArea
          rows={3}
          placeholder="Yechim izohi (ixtiyoriy)"
          value={resolutionComment}
          onChange={(e) => setResolutionComment(e.target.value)}
        />
      </Modal>

      <Modal
        title={`Qayta yo'naltirish — #${reassignTarget?.ticket_number ?? ""}`}
        open={reassignTarget !== null}
        onCancel={() => setReassignTarget(null)}
        onOk={handleReassign}
        confirmLoading={actionLoading}
        okText="Yo'naltirish"
        cancelText="Bekor qilish"
        okButtonProps={{ disabled: !reassignTechnicianId }}
      >
        <Select
          style={{ width: "100%" }}
          placeholder="Texnik xodimni tanlang"
          value={reassignTechnicianId}
          onChange={setReassignTechnicianId}
          options={(reassignTarget ? technicianOptionsForFaculty(reassignTarget.faculty_id) : [])
            .filter((t) => t.id !== reassignTarget?.assigned_technician_id)
            .map((t) => ({ label: t.full_name, value: t.id }))}
        />
      </Modal>
    </div>
  );
}

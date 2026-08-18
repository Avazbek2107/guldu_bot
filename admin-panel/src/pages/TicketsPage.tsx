import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Button,
  Card,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
  message,
} from "antd";
import { FileExcelOutlined, FilePdfOutlined, PaperClipOutlined } from "@ant-design/icons";
import { downloadTicketPdf, resolveAssetUrl } from "../api/client";
import { closeTicket, exportTickets, listTickets, reassignTicket, type TicketFilters } from "../api/tickets";
import { listFaculties } from "../api/faculties";
import { listInventory } from "../api/inventory";
import { listUsers } from "../api/users";
import { ActionsMenu, type ActionItem } from "../components/ActionsMenu";
import { CARD_STYLE } from "../theme";
import { useAuth } from "../auth/AuthContext";
import { hasPermission } from "../auth/permissions";
import {
  CATEGORY_LABELS_UZ,
  orgUnitLabel,
  PRIORITY_LABELS_UZ,
  STATUS_LABELS_UZ,
  type FacultyOut,
  type InventoryItemOut,
  type TicketCategory,
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
  const isTechnician = user?.role === "technician_main" || user?.role === "technician_backup";
  const canEdit = isTechnician || hasPermission(user, "tickets", "edit");
  // Super Admin and any Admin granted "tickets" view see every faculty's tickets
  // (unlike technicians, who are always scoped to their own faculty by the
  // backend) — so they need the faculty filter/column to tell them apart.
  const canSeeAllFaculties = isSuperAdmin || hasPermission(user, "tickets");
  const [searchParams] = useSearchParams();

  const [tickets, setTickets] = useState<TicketOut[]>([]);
  const [faculties, setFaculties] = useState<FacultyOut[]>([]);
  const [technicians, setTechnicians] = useState<UserOut[]>([]);
  const [loading, setLoading] = useState(true);

  const [facultyFilter, setFacultyFilter] = useState<number | undefined>();
  const [statusFilter, setStatusFilter] = useState<TicketStatus | undefined>(
    () => (searchParams.get("status") as TicketStatus | null) ?? undefined,
  );
  const [categoryFilter, setCategoryFilter] = useState<TicketCategory | undefined>();

  const [closeTarget, setCloseTarget] = useState<TicketOut | null>(null);
  const [resolutionComment, setResolutionComment] = useState("");
  const [closeInventoryOptions, setCloseInventoryOptions] = useState<InventoryItemOut[]>([]);
  const [closeInventoryId, setCloseInventoryId] = useState<number | undefined>();
  const [closeInventoryLoading, setCloseInventoryLoading] = useState(false);
  const [reassignTarget, setReassignTarget] = useState<TicketOut | null>(null);
  const [reassignTechnicianId, setReassignTechnicianId] = useState<number | undefined>();
  const [actionLoading, setActionLoading] = useState(false);
  const requestIdRef = useRef(0);

  const currentFilters: TicketFilters = {
    faculty_id: facultyFilter,
    status: statusFilter,
    category: categoryFilter,
  };

  async function loadTickets() {
    const requestId = ++requestIdRef.current;
    setLoading(true);
    try {
      const data = await listTickets(currentFilters);
      if (requestId === requestIdRef.current) {
        setTickets(data);
      }
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }

  const [exportLoading, setExportLoading] = useState(false);
  const [pdfLoadingId, setPdfLoadingId] = useState<number | null>(null);

  async function handlePdfDownload(record: TicketOut) {
    setPdfLoadingId(record.id);
    try {
      await downloadTicketPdf(record.id, `${record.ticket_number}.pdf`);
    } catch {
      message.error("Ma'lumotnomani yuklab olishda xatolik yuz berdi");
    } finally {
      setPdfLoadingId(null);
    }
  }

  async function handleExport(format: "xlsx" | "pdf") {
    setExportLoading(true);
    try {
      await exportTickets(currentFilters, format);
    } catch {
      message.error("Eksport qilishda xatolik yuz berdi");
    } finally {
      setExportLoading(false);
    }
  }

  useEffect(() => {
    listFaculties(undefined, { topLevel: true }).then(setFaculties);
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
    () => (facultyId: number) =>
      technicians.filter((t) => (t.faculty_assignments ?? []).some((a) => a.faculty_id === facultyId)),
    [technicians],
  );

  async function openCloseModal(record: TicketOut) {
    setCloseTarget(record);
    setCloseInventoryId(undefined);
    setCloseInventoryOptions([]);
    setCloseInventoryLoading(true);
    try {
      setCloseInventoryOptions(await listInventory(record.faculty_id));
    } finally {
      setCloseInventoryLoading(false);
    }
  }

  async function handleClose() {
    if (!closeTarget || !closeInventoryId) return;
    setActionLoading(true);
    try {
      await closeTicket(closeTarget.id, resolutionComment || null, closeInventoryId);
      message.success(`Ariza #${closeTarget.ticket_number} yopildi`);
      setCloseTarget(null);
      setResolutionComment("");
      setCloseInventoryId(undefined);
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
        {canSeeAllFaculties && (
          <Select
            allowClear
            placeholder="Fakultet"
            style={{ width: 180 }}
            value={facultyFilter}
            onChange={setFacultyFilter}
            options={faculties.map((f) => ({ label: orgUnitLabel(f), value: f.id }))}
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
        <Button icon={<FileExcelOutlined />} loading={exportLoading} onClick={() => handleExport("xlsx")}>
          Excel
        </Button>
        <Button icon={<FilePdfOutlined />} loading={exportLoading} onClick={() => handleExport("pdf")}>
          PDF
        </Button>
      </Space>

      <Card style={CARD_STYLE}>
      <Table
        rowKey="id"
        loading={loading}
        scroll={{ x: "max-content" }}
        dataSource={tickets}
        columns={[
          { title: "Ariza №", dataIndex: "ticket_number" },
          { title: "FISH", dataIndex: "creator_full_name" },
          { title: "Telefon", dataIndex: "creator_phone" },
          ...(canSeeAllFaculties ? [{ title: "Fakultet", dataIndex: "faculty_name" }] : []),
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
            title: "Bildirishnoma",
            key: "closing_attachment",
            render: (_: unknown, record: TicketOut) =>
              record.closing_attachment_url ? (
                <Tooltip title="Bildirishnomani yuklab olish">
                  <a
                    href={resolveAssetUrl(record.closing_attachment_url)}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Button size="small" icon={<PaperClipOutlined />} />
                  </a>
                </Tooltip>
              ) : (
                "-"
              ),
          },
          {
            title: "Sana",
            dataIndex: "created_at",
            render: (v: string) => new Date(v).toLocaleString("uz-UZ"),
          },
          {
            title: "Amallar",
            key: "actions",
            fixed: "right",
            width: 96,
            render: (_: unknown, record: TicketOut) => {
              const menuItems: ActionItem[] =
                record.status !== "closed" && canEdit
                  ? [
                      { key: "close", label: "Yopish", onClick: () => openCloseModal(record) },
                      { key: "reassign", label: "Qayta yo'naltirish", onClick: () => setReassignTarget(record) },
                    ]
                  : [];
              return (
                <Space size={4}>
                  <Tooltip title="Ma'lumotnomani yuklab olish">
                    <Button
                      size="small"
                      icon={<FilePdfOutlined />}
                      loading={pdfLoadingId === record.id}
                      onClick={() => handlePdfDownload(record)}
                    />
                  </Tooltip>
                  {menuItems.length > 0 && <ActionsMenu items={menuItems} />}
                </Space>
              );
            },
          },
        ]}
      />
      </Card>

      <Modal
        title={`Arizani yopish — #${closeTarget?.ticket_number ?? ""}`}
        open={closeTarget !== null}
        onCancel={() => setCloseTarget(null)}
        onOk={handleClose}
        confirmLoading={actionLoading}
        okText="Yopish"
        cancelText="Bekor qilish"
        okButtonProps={{ disabled: !closeInventoryId }}
      >
        <div style={{ marginBottom: 12 }}>
          <div style={{ marginBottom: 4 }}>
            Ta'mirlangan qurilma (inventar) <span style={{ color: "red" }}>*</span>
          </div>
          <Select
            showSearch
            allowClear
            loading={closeInventoryLoading}
            style={{ width: "100%" }}
            placeholder="Inventarni tanlang"
            value={closeInventoryId}
            onChange={setCloseInventoryId}
            filterOption={(input, option) =>
              (option?.label as string | undefined)?.toLowerCase().includes(input.toLowerCase()) ?? false
            }
            options={closeInventoryOptions.map((item) => ({
              value: item.id,
              label: `${item.room ?? "xonasiz"} — ${item.inventory_number ?? "raqamsiz"} (${item.model ?? item.inventory_type ?? "?"})`,
            }))}
            notFoundContent={
              closeInventoryLoading ? undefined : "Bu fakultetda inventar topilmadi. Avval Inventar sahifasida qo'shing."
            }
          />
        </div>
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

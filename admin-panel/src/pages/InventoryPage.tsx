import { useEffect, useRef, useState, type ChangeEvent } from "react";
import {
  Button,
  Card,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  TreeSelect,
  Typography,
  message,
} from "antd";
import { DownloadOutlined, HistoryOutlined, PlusOutlined, UploadOutlined } from "@ant-design/icons";
import {
  createInventoryItem,
  deleteInventoryItem,
  exportInventory,
  getInventoryHistory,
  importInventory,
  listInventory,
  updateInventoryItem,
  type InventoryItemPayload,
} from "../api/inventory";
import { listFaculties } from "../api/faculties";
import { listUsers } from "../api/users";
import { ActionsMenu } from "../components/ActionsMenu";
import { CARD_STYLE } from "../theme";
import { useAuth } from "../auth/AuthContext";
import { hasPermission } from "../auth/permissions";
import { INVENTORY_TYPES } from "../types";
import type { FacultyOut, InventoryItemOut, RepairHistoryItem, UserOut } from "../types";

const STATUS_OPTIONS = [
  { value: "Ishchi", label: "Ishchi" },
  { value: "Ta'mir talab", label: "Ta'mir talab" },
  { value: "Yaroqsiz", label: "Yaroqsiz" },
];

const INTERNET_OPTIONS = [
  { value: "Internetga ulangan (kabeli bor)", label: "Internetga ulangan (kabeli bor)" },
  { value: "Internetga ulanmagan (kabeli yo'q)", label: "Internetga ulanmagan (kabeli yo'q)" },
  { value: "Wifi", label: "Wifi" },
];

const STATUS_COLORS: Record<string, string> = {
  Ishchi: "green",
  "Ta'mir talab": "orange",
  Yaroqsiz: "red",
};

const INVENTORY_TYPE_OPTIONS = INVENTORY_TYPES.map((v) => ({ value: v, label: v }));

const MAC_ADDRESS_TYPES = new Set(["Monoblok", "Kompyuter", "Noutbook", "Interaktiv panel"]);

interface LocationTreeNode {
  title: string;
  value: number;
  children?: LocationTreeNode[];
}

export function InventoryPage() {
  const { user } = useAuth();
  const isTechnician = user?.role === "technician_main" || user?.role === "technician_backup";
  const canCreate = isTechnician || hasPermission(user, "inventory", "create");
  const canEdit = isTechnician || hasPermission(user, "inventory", "edit");
  const canDelete = isTechnician || hasPermission(user, "inventory", "delete");

  const [items, setItems] = useState<InventoryItemOut[]>([]);
  const [locationTree, setLocationTree] = useState<LocationTreeNode[]>([]);
  const [kafedras, setKafedras] = useState<FacultyOut[]>([]);
  const [technicians, setTechnicians] = useState<UserOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [facultyFilter, setFacultyFilter] = useState<number | undefined>();

  const [createOpen, setCreateOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<InventoryItemOut | null>(null);
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();
  const [saving, setSaving] = useState(false);
  const createFacultyId = Form.useWatch("faculty_id", createForm);
  const editFacultyId = Form.useWatch("faculty_id", editForm);
  const createInventoryType = Form.useWatch("inventory_type", createForm);
  const editInventoryType = Form.useWatch("inventory_type", editForm);

  const [historyTarget, setHistoryTarget] = useState<InventoryItemOut | null>(null);
  const [history, setHistory] = useState<RepairHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const [exportLoading, setExportLoading] = useState(false);
  const [importLoading, setImportLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const requestIdRef = useRef(0);

  async function loadData() {
    const requestId = ++requestIdRef.current;
    setLoading(true);
    try {
      const [itemList, facultyList, departmentList, mainTechs, backupTechs] = await Promise.all([
        listInventory(facultyFilter),
        listFaculties("faculty"),
        listFaculties("department"),
        listUsers({ role: "technician_main" }),
        listUsers({ role: "technician_backup" }),
      ]);
      if (requestId === requestIdRef.current) {
        const topLevelDepartments = departmentList.filter((d) => d.parent_id == null);
        const kafedraList = departmentList.filter((d) => d.parent_id != null);
        setItems(itemList);
        setKafedras(kafedraList);
        setLocationTree([
          ...facultyList.map((f) => ({
            title: f.name,
            value: f.id,
            children: kafedraList
              .filter((k) => k.parent_id === f.id)
              .map((k) => ({ title: k.name, value: k.id })),
          })),
          ...topLevelDepartments.map((d) => ({ title: `${d.name} (bo'lim)`, value: d.id })),
        ]);
        setTechnicians([...mainTechs, ...backupTechs]);
      }
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [facultyFilter]);

  function resolveScopeFacultyId(facultyId: number | undefined): number | undefined {
    if (facultyId == null) return undefined;
    const kafedra = kafedras.find((k) => k.id === facultyId);
    return kafedra ? kafedra.parent_id ?? facultyId : facultyId;
  }

  function technicianOptionsForFaculty(facultyId: number | undefined) {
    const scopeId = resolveScopeFacultyId(facultyId);
    if (!scopeId) return [];
    return technicians
      .map((t) => {
        const assignment = (t.faculty_assignments ?? []).find((a) => a.faculty_id === scopeId);
        if (!assignment) return null;
        return {
          value: t.id,
          label: `${t.full_name} (${assignment.role === "technician_main" ? "asosiy" : "zaxira"})`,
        };
      })
      .filter((opt): opt is { value: number; label: string } => opt !== null);
  }

  async function handleCreate(values: InventoryItemPayload) {
    setSaving(true);
    try {
      await createInventoryItem(values);
      message.success("Inventar qo'shildi");
      setCreateOpen(false);
      createForm.resetFields();
      loadData();
    } catch {
      message.error("Xatolik yuz berdi");
    } finally {
      setSaving(false);
    }
  }

  async function handleEditSave(values: Partial<InventoryItemPayload>) {
    if (!editTarget) return;
    setSaving(true);
    try {
      await updateInventoryItem(editTarget.id, {
        ...values,
        assigned_technician_id: values.assigned_technician_id ?? null,
      });
      message.success("Saqlandi");
      setEditTarget(null);
      loadData();
    } catch {
      message.error("Xatolik yuz berdi");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(item: InventoryItemOut) {
    try {
      await deleteInventoryItem(item.id);
      message.success("O'chirildi");
      loadData();
    } catch {
      message.error("Xatolik yuz berdi");
    }
  }

  async function openHistory(item: InventoryItemOut) {
    setHistoryTarget(item);
    setHistoryLoading(true);
    try {
      setHistory(await getInventoryHistory(item.id));
    } finally {
      setHistoryLoading(false);
    }
  }

  async function handleExport() {
    setExportLoading(true);
    try {
      await exportInventory(facultyFilter);
    } catch {
      message.error("Eksport qilishda xatolik yuz berdi");
    } finally {
      setExportLoading(false);
    }
  }

  async function handleImportFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setImportLoading(true);
    try {
      const result = await importInventory(file);
      if (result.skipped.length === 0) {
        message.success(`${result.created} ta inventar qo'shildi`);
      } else {
        Modal.warning({
          title: `${result.created} ta qo'shildi, ${result.skipped.length} ta qator o'tkazib yuborildi`,
          content: (
            <div style={{ maxHeight: 300, overflowY: "auto" }}>
              {result.skipped.map((s) => (
                <div key={s.row}>
                  Qator {s.row}: {s.reason}
                </div>
              ))}
            </div>
          ),
          width: 480,
        });
      }
      loadData();
    } catch {
      message.error("Import qilishda xatolik yuz berdi");
    } finally {
      setImportLoading(false);
    }
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }} wrap>
        <TreeSelect
          allowClear
          showSearch
          treeNodeFilterProp="title"
          placeholder="Fakultet/bo'lim bo'yicha filtrlash"
          style={{ width: 280 }}
          value={facultyFilter}
          onChange={setFacultyFilter}
          treeData={locationTree}
        />
        {canCreate && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
            Yangi inventar
          </Button>
        )}
        {canCreate && (
          <Button icon={<UploadOutlined />} loading={importLoading} onClick={() => fileInputRef.current?.click()}>
            Import (Excel)
          </Button>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx"
          style={{ display: "none" }}
          onChange={handleImportFile}
        />
        <Button icon={<DownloadOutlined />} loading={exportLoading} onClick={handleExport}>
          Export (Excel)
        </Button>
      </Space>

      <Card style={CARD_STYLE}>
      <Table
        rowKey="id"
        loading={loading}
        scroll={{ x: "max-content" }}
        dataSource={items}
        columns={[
          { title: "Fakultet yoki Bo'lim", dataIndex: "faculty_name" },
          { title: "Xona", dataIndex: "room", render: (v: string | null) => v ?? "-" },
          { title: "Inventar №", dataIndex: "inventory_number", render: (v: string | null) => v ?? "-" },
          { title: "Inventar uzasbo", dataIndex: "uzasbo", render: (v: string | null) => v ?? "-" },
          { title: "Toifasi", dataIndex: "inventory_type", render: (v: string | null) => v ?? "-" },
          { title: "Modeli", dataIndex: "model", render: (v: string | null) => v ?? "-" },
          {
            title: "Xolati",
            dataIndex: "status",
            render: (v: string) => <Tag color={STATUS_COLORS[v] ?? "default"}>{v}</Tag>,
          },
          { title: "Internet", dataIndex: "internet_connection", render: (v: string | null) => v ?? "-" },
          { title: "MAC manzili", dataIndex: "mac_address", render: (v: string | null) => v ?? "-" },
          { title: "Mas'ul shaxs", dataIndex: "responsible_person", render: (v: string | null) => v ?? "-" },
          {
            title: "Texnik xodim",
            dataIndex: "assigned_technician_name",
            render: (v: string | null) => v ?? "-",
          },
          {
            title: "Ta'mirlangan",
            dataIndex: "repair_count",
            render: (v: number) => (v > 0 ? <Tag color="blue">{v} marta</Tag> : "-"),
          },
          {
            title: "Amallar",
            key: "actions",
            fixed: "right",
            width: 72,
            render: (_: unknown, record: InventoryItemOut) => (
              <ActionsMenu
                items={[
                  {
                    key: "history",
                    label: "Tarix",
                    icon: <HistoryOutlined />,
                    onClick: () => openHistory(record),
                  },
                  ...(canEdit
                    ? [
                        {
                          key: "edit",
                          label: "Tahrirlash",
                          onClick: () => {
                            setEditTarget(record);
                            editForm.setFieldsValue({
                              faculty_id: record.faculty_id,
                              room: record.room ?? undefined,
                              inventory_number: record.inventory_number ?? undefined,
                              uzasbo: record.uzasbo ?? undefined,
                              inventory_type: record.inventory_type ?? undefined,
                              model: record.model ?? undefined,
                              status: record.status,
                              internet_connection: record.internet_connection ?? undefined,
                              mac_address: record.mac_address ?? undefined,
                              responsible_person: record.responsible_person ?? undefined,
                              assigned_technician_id: record.assigned_technician_id ?? undefined,
                            });
                          },
                        },
                      ]
                    : []),
                  ...(canDelete
                    ? [
                        {
                          key: "delete",
                          label: "O'chirish",
                          danger: true,
                          confirmTitle: "O'chirishni tasdiqlaysizmi?",
                          onClick: () => handleDelete(record),
                        },
                      ]
                    : []),
                ]}
              />
            ),
          },
        ]}
      />
      </Card>

      <Modal
        title="Yangi inventar"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => createForm.submit()}
        confirmLoading={saving}
        okText="Qo'shish"
        cancelText="Bekor qilish"
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreate} initialValues={{ status: "Ishchi" }}>
          <Form.Item name="faculty_id" label="Fakultet yoki Bo'lim" rules={[{ required: true }]}>
            <TreeSelect
              showSearch
              treeNodeFilterProp="title"
              treeData={locationTree}
              onChange={() => createForm.setFieldValue("assigned_technician_id", undefined)}
            />
          </Form.Item>
          <Form.Item name="room" label="Xona">
            <Input />
          </Form.Item>
          <Form.Item name="inventory_number" label="Inventar raqami">
            <Input />
          </Form.Item>
          <Form.Item name="uzasbo" label="Inventar uzash sababi/varaqasi">
            <Input />
          </Form.Item>
          <Form.Item name="inventory_type" label="Inventar toifasi">
            <Select allowClear options={INVENTORY_TYPE_OPTIONS} />
          </Form.Item>
          <Form.Item name="model" label="Modeli">
            <Input />
          </Form.Item>
          <Form.Item name="status" label="Xolati">
            <Select options={STATUS_OPTIONS} />
          </Form.Item>
          <Form.Item name="internet_connection" label="Internetga ulanganligi">
            <Select allowClear options={INTERNET_OPTIONS} />
          </Form.Item>
          {createInventoryType && MAC_ADDRESS_TYPES.has(createInventoryType) && (
            <Form.Item name="mac_address" label="MAC manzili">
              <Input placeholder="Masalan: AA:BB:CC:DD:EE:FF" />
            </Form.Item>
          )}
          <Form.Item name="responsible_person" label="Mas'ul shaxs">
            <Input />
          </Form.Item>
          <Form.Item
            name="assigned_technician_id"
            label="Texnik xodim"
            extra="Fakultet/bo'lim o'zgartirilsa, tanlangan texnik xodim tozalanadi"
          >
            <Select
              allowClear
              showSearch
              optionFilterProp="label"
              placeholder="Avtomatik (hudud asosiy texnik xodimi)"
              options={technicianOptionsForFaculty(createFacultyId)}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`Tahrirlash — ${editTarget?.inventory_number ?? editTarget?.room ?? ""}`}
        open={editTarget !== null}
        onCancel={() => setEditTarget(null)}
        onOk={() => editForm.submit()}
        confirmLoading={saving}
        okText="Saqlash"
        cancelText="Bekor qilish"
      >
        <Form form={editForm} layout="vertical" onFinish={handleEditSave}>
          <Form.Item name="faculty_id" label="Fakultet yoki Bo'lim" rules={[{ required: true }]}>
            <TreeSelect
              showSearch
              treeNodeFilterProp="title"
              treeData={locationTree}
              onChange={() => editForm.setFieldValue("assigned_technician_id", undefined)}
            />
          </Form.Item>
          <Form.Item name="room" label="Xona">
            <Input />
          </Form.Item>
          <Form.Item name="inventory_number" label="Inventar raqami">
            <Input />
          </Form.Item>
          <Form.Item name="uzasbo" label="Inventar uzash sababi/varaqasi">
            <Input />
          </Form.Item>
          <Form.Item name="inventory_type" label="Inventar toifasi">
            <Select allowClear options={INVENTORY_TYPE_OPTIONS} />
          </Form.Item>
          <Form.Item name="model" label="Modeli">
            <Input />
          </Form.Item>
          <Form.Item name="status" label="Xolati">
            <Select options={STATUS_OPTIONS} />
          </Form.Item>
          <Form.Item name="internet_connection" label="Internetga ulanganligi">
            <Select allowClear options={INTERNET_OPTIONS} />
          </Form.Item>
          {editInventoryType && MAC_ADDRESS_TYPES.has(editInventoryType) && (
            <Form.Item name="mac_address" label="MAC manzili">
              <Input placeholder="Masalan: AA:BB:CC:DD:EE:FF" />
            </Form.Item>
          )}
          <Form.Item name="responsible_person" label="Mas'ul shaxs">
            <Input />
          </Form.Item>
          <Form.Item
            name="assigned_technician_id"
            label="Texnik xodim"
            extra="Fakultet/bo'lim o'zgartirilsa, tanlangan texnik xodim tozalanadi"
          >
            <Select
              allowClear
              showSearch
              optionFilterProp="label"
              placeholder="Avtomatik (hudud asosiy texnik xodimi)"
              options={technicianOptionsForFaculty(editFacultyId)}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`Ta'mirlanish tarixi — ${historyTarget?.inventory_number ?? historyTarget?.room ?? ""}`}
        open={historyTarget !== null}
        onCancel={() => setHistoryTarget(null)}
        footer={null}
      >
        <Typography.Paragraph>
          Jami: <strong>{history.length}</strong> marta ta'mirlangan
        </Typography.Paragraph>
        <Table
          size="small"
          rowKey="ticket_id"
          loading={historyLoading}
          pagination={false}
          dataSource={history}
          columns={[
            { title: "Ariza №", dataIndex: "ticket_number" },
            {
              title: "Yopilgan sana",
              dataIndex: "closed_at",
              render: (v: string | null) => (v ? new Date(v).toLocaleDateString("uz-UZ") : "-"),
            },
            { title: "Texnik", dataIndex: "technician_full_name", render: (v: string | null) => v ?? "-" },
            { title: "Izoh", dataIndex: "resolution_comment", render: (v: string | null) => v ?? "-" },
          ]}
        />
      </Modal>
    </div>
  );
}

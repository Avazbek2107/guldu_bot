import { useEffect, useRef, useState, type ChangeEvent } from "react";
import {
  Button,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
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
import { ActionsMenu } from "../components/ActionsMenu";
import { orgUnitLabel, type FacultyOut, type InventoryItemOut, type RepairHistoryItem } from "../types";

const STATUS_OPTIONS = [
  { value: "ishchi", label: "Ishchi" },
  { value: "nosoz", label: "Nosoz" },
  { value: "ta'mirlanmoqda", label: "Ta'mirlanmoqda" },
  { value: "hisobdan chiqarilgan", label: "Hisobdan chiqarilgan" },
];

const STATUS_COLORS: Record<string, string> = {
  ishchi: "green",
  nosoz: "red",
  "ta'mirlanmoqda": "orange",
  "hisobdan chiqarilgan": "default",
};

export function InventoryPage() {
  const [items, setItems] = useState<InventoryItemOut[]>([]);
  const [faculties, setFaculties] = useState<FacultyOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [facultyFilter, setFacultyFilter] = useState<number | undefined>();

  const [createOpen, setCreateOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<InventoryItemOut | null>(null);
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();
  const [saving, setSaving] = useState(false);

  const [historyTarget, setHistoryTarget] = useState<InventoryItemOut | null>(null);
  const [history, setHistory] = useState<RepairHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const [exportLoading, setExportLoading] = useState(false);
  const [importLoading, setImportLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  async function loadData() {
    setLoading(true);
    try {
      const [itemList, facultyList] = await Promise.all([listInventory(facultyFilter), listFaculties()]);
      setItems(itemList);
      setFaculties(facultyList);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [facultyFilter]);

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
      await updateInventoryItem(editTarget.id, values);
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
        <Select
          allowClear
          placeholder="Fakultet/bo'lim bo'yicha filtrlash"
          style={{ width: 260 }}
          value={facultyFilter}
          onChange={setFacultyFilter}
          options={faculties.map((f) => ({ value: f.id, label: orgUnitLabel(f) }))}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          Yangi inventar
        </Button>
        <Button icon={<UploadOutlined />} loading={importLoading} onClick={() => fileInputRef.current?.click()}>
          Import (Excel)
        </Button>
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

      <Table
        rowKey="id"
        loading={loading}
        scroll={{ x: "max-content" }}
        dataSource={items}
        columns={[
          { title: "Fakultet/Bo'lim", dataIndex: "faculty_name" },
          { title: "Kafedra/Bo'lim", dataIndex: "sub_unit", render: (v: string | null) => v ?? "-" },
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
          { title: "Mas'ul shaxs", dataIndex: "responsible_person", render: (v: string | null) => v ?? "-" },
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
                  {
                    key: "edit",
                    label: "Tahrirlash",
                    onClick: () => {
                      setEditTarget(record);
                      editForm.setFieldsValue({
                        faculty_id: record.faculty_id,
                        sub_unit: record.sub_unit ?? undefined,
                        room: record.room ?? undefined,
                        inventory_number: record.inventory_number ?? undefined,
                        uzasbo: record.uzasbo ?? undefined,
                        inventory_type: record.inventory_type ?? undefined,
                        model: record.model ?? undefined,
                        status: record.status,
                        internet_connection: record.internet_connection ?? undefined,
                        responsible_person: record.responsible_person ?? undefined,
                      });
                    },
                  },
                  {
                    key: "delete",
                    label: "O'chirish",
                    danger: true,
                    confirmTitle: "O'chirishni tasdiqlaysizmi?",
                    onClick: () => handleDelete(record),
                  },
                ]}
              />
            ),
          },
        ]}
      />

      <Modal
        title="Yangi inventar"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => createForm.submit()}
        confirmLoading={saving}
        okText="Qo'shish"
        cancelText="Bekor qilish"
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreate} initialValues={{ status: "ishchi" }}>
          <Form.Item name="faculty_id" label="Fakultet/Bo'lim" rules={[{ required: true }]}>
            <Select options={faculties.map((f) => ({ value: f.id, label: orgUnitLabel(f) }))} />
          </Form.Item>
          <Form.Item name="sub_unit" label="Kafedra/Bo'lim">
            <Input />
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
            <Input placeholder="Monoblok, Printer va h.k." />
          </Form.Item>
          <Form.Item name="model" label="Modeli">
            <Input />
          </Form.Item>
          <Form.Item name="status" label="Xolati">
            <Select options={STATUS_OPTIONS} />
          </Form.Item>
          <Form.Item name="internet_connection" label="Internetga ulanganligi">
            <Input placeholder="Masalan: internetga ulangan (kabeli bor)" />
          </Form.Item>
          <Form.Item name="responsible_person" label="Mas'ul shaxs">
            <Input />
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
          <Form.Item name="faculty_id" label="Fakultet/Bo'lim" rules={[{ required: true }]}>
            <Select options={faculties.map((f) => ({ value: f.id, label: orgUnitLabel(f) }))} />
          </Form.Item>
          <Form.Item name="sub_unit" label="Kafedra/Bo'lim">
            <Input />
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
            <Input />
          </Form.Item>
          <Form.Item name="model" label="Modeli">
            <Input />
          </Form.Item>
          <Form.Item name="status" label="Xolati">
            <Select options={STATUS_OPTIONS} />
          </Form.Item>
          <Form.Item name="internet_connection" label="Internetga ulanganligi">
            <Input />
          </Form.Item>
          <Form.Item name="responsible_person" label="Mas'ul shaxs">
            <Input />
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

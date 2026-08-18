import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { Button, Card, Form, Input, Modal, Space, Table, Tag, message } from "antd";
import { DownloadOutlined, PlusOutlined, UploadOutlined } from "@ant-design/icons";
import {
  createFaculty,
  deleteFaculty,
  exportFaculties,
  importFaculties,
  listFaculties,
  updateFaculty,
} from "../api/faculties";
import { listUsers } from "../api/users";
import { ActionsMenu, type ActionItem } from "../components/ActionsMenu";
import { CARD_STYLE } from "../theme";
import { useAuth } from "../auth/AuthContext";
import { hasPermission } from "../auth/permissions";
import type { FacultyOut, UserOut } from "../types";

interface FacultyRow extends FacultyOut {
  children?: FacultyRow[];
}

export function FacultiesPage() {
  const { user } = useAuth();
  const canCreate = hasPermission(user, "faculties", "create");
  const canEdit = hasPermission(user, "faculties", "edit");
  const canDeleteFaculty = hasPermission(user, "faculties", "delete");
  const canManageKafedra = hasPermission(user, "departments", "edit");
  const canDeleteKafedra = hasPermission(user, "departments", "delete");

  const [faculties, setFaculties] = useState<FacultyOut[]>([]);
  const [kafedras, setKafedras] = useState<FacultyOut[]>([]);
  const [technicians, setTechnicians] = useState<UserOut[]>([]);
  const [loading, setLoading] = useState(true);

  const [createOpen, setCreateOpen] = useState(false);
  const [kafedraTarget, setKafedraTarget] = useState<FacultyOut | null>(null);
  const [renameTarget, setRenameTarget] = useState<FacultyOut | null>(null);
  const [createForm] = Form.useForm();
  const [kafedraForm] = Form.useForm();
  const [renameForm] = Form.useForm();
  const [saving, setSaving] = useState(false);

  const [exportLoading, setExportLoading] = useState(false);
  const [importLoading, setImportLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  async function loadData() {
    setLoading(true);
    try {
      const [facultyList, departmentList, mainTechs, backupTechs] = await Promise.all([
        listFaculties("faculty"),
        listFaculties("department"),
        listUsers({ role: "technician_main" }),
        listUsers({ role: "technician_backup" }),
      ]);
      setFaculties(facultyList);
      setKafedras(departmentList.filter((d) => d.parent_id != null));
      setTechnicians([...mainTechs, ...backupTechs]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function techniciansFor(orgUnitId: number, role: "technician_main" | "technician_backup") {
    const names = technicians
      .filter((t) => (t.faculty_assignments ?? []).some((a) => a.faculty_id === orgUnitId && a.role === role))
      .map((t) => t.full_name);
    return names.length > 0 ? names.join(", ") : "-";
  }

  const treeData: FacultyRow[] = faculties.map((f) => {
    const children = kafedras.filter((k) => k.parent_id === f.id);
    return children.length > 0 ? { ...f, children } : { ...f };
  });

  async function handleCreate(values: { name: string }) {
    setSaving(true);
    try {
      await createFaculty(values.name);
      message.success("Fakultet qo'shildi");
      setCreateOpen(false);
      createForm.resetFields();
      loadData();
    } catch {
      message.error("Xatolik yuz berdi");
    } finally {
      setSaving(false);
    }
  }

  async function handleCreateKafedra(values: { name: string }) {
    if (!kafedraTarget) return;
    setSaving(true);
    try {
      await createFaculty(values.name, "department", kafedraTarget.id);
      message.success("Kafedra qo'shildi");
      setKafedraTarget(null);
      kafedraForm.resetFields();
      loadData();
    } catch {
      message.error("Xatolik yuz berdi");
    } finally {
      setSaving(false);
    }
  }

  async function handleRename(values: { name: string }) {
    if (!renameTarget) return;
    setSaving(true);
    try {
      await updateFaculty(renameTarget.id, values.name);
      message.success("Saqlandi");
      setRenameTarget(null);
      loadData();
    } catch {
      message.error("Xatolik yuz berdi");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(record: FacultyOut) {
    try {
      await deleteFaculty(record.id);
      message.success("O'chirildi");
      loadData();
    } catch {
      message.error(
        "O'chirib bo'lmadi: bunga bog'liq xodimlar, arizalar yoki inventar mavjud (yoki kafedralarni avval o'chiring)",
      );
    }
  }

  async function handleExport() {
    setExportLoading(true);
    try {
      await exportFaculties("faculty");
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
      const result = await importFaculties("faculty", file);
      if (result.skipped.length === 0) {
        message.success(`${result.created} ta fakultet qo'shildi`);
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
        {canCreate && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
            Yangi fakultet
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
      <Table<FacultyRow>
        rowKey="id"
        loading={loading}
        scroll={{ x: "max-content" }}
        dataSource={treeData}
        pagination={false}
        columns={[
          {
            title: "Nomi",
            dataIndex: "name",
            render: (name: string, record: FacultyRow) =>
              record.parent_id != null ? (
                <Space>
                  <Tag color="default">Kafedra</Tag>
                  {name}
                </Space>
              ) : (
                name
              ),
          },
          {
            title: "Asosiy texnik xodim",
            key: "main",
            render: (_: unknown, record: FacultyRow) =>
              record.parent_id != null ? "-" : techniciansFor(record.id, "technician_main"),
          },
          {
            title: "Zaxira texnik xodim",
            key: "backup",
            render: (_: unknown, record: FacultyRow) =>
              record.parent_id != null ? "-" : techniciansFor(record.id, "technician_backup"),
          },
          {
            title: "Amallar",
            key: "actions",
            render: (_: unknown, record: FacultyRow) => {
              const isKafedra = record.parent_id != null;
              const canRename = isKafedra ? canManageKafedra : canEdit;
              const canDelete = isKafedra ? canDeleteKafedra : canDeleteFaculty;
              const items: ActionItem[] = [];
              if (canRename) {
                items.push({
                  key: "rename",
                  label: "Nomini o'zgartirish",
                  onClick: () => {
                    setRenameTarget(record);
                    renameForm.setFieldsValue({ name: record.name });
                  },
                });
              }
              if (!isKafedra && canManageKafedra) {
                items.push({
                  key: "add-kafedra",
                  label: "Yangi kafedra",
                  onClick: () => {
                    setKafedraTarget(record);
                    kafedraForm.resetFields();
                  },
                });
              }
              if (canDelete) {
                items.push({
                  key: "delete",
                  label: "O'chirish",
                  danger: true,
                  confirmTitle: isKafedra
                    ? "Kafedrani o'chirishni tasdiqlaysizmi?"
                    : "Fakultetni va unga tegishli barcha kafedralarni o'chirishni tasdiqlaysizmi?",
                  onClick: () => handleDelete(record),
                });
              }
              return items.length > 0 ? <ActionsMenu items={items} /> : null;
            },
          },
        ]}
      />
      </Card>

      <Modal
        title="Yangi fakultet"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => createForm.submit()}
        confirmLoading={saving}
        okText="Qo'shish"
        cancelText="Bekor qilish"
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="Fakultet nomi" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`Yangi kafedra — ${kafedraTarget?.name ?? ""}`}
        open={kafedraTarget !== null}
        onCancel={() => setKafedraTarget(null)}
        onOk={() => kafedraForm.submit()}
        confirmLoading={saving}
        okText="Qo'shish"
        cancelText="Bekor qilish"
      >
        <Form form={kafedraForm} layout="vertical" onFinish={handleCreateKafedra}>
          <Form.Item name="name" label="Kafedra nomi" rules={[{ required: true }]}>
            <Input placeholder="Masalan: Fizika kafedrasi" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`Nomini o'zgartirish — ${renameTarget?.name ?? ""}`}
        open={renameTarget !== null}
        onCancel={() => setRenameTarget(null)}
        onOk={() => renameForm.submit()}
        confirmLoading={saving}
        okText="Saqlash"
        cancelText="Bekor qilish"
      >
        <Form form={renameForm} layout="vertical" onFinish={handleRename}>
          <Form.Item name="name" label="Nomi" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { Button, Card, Form, Input, Modal, Space, Table, message } from "antd";
import { DownloadOutlined, PlusOutlined, UploadOutlined } from "@ant-design/icons";
import {
  createFaculty,
  deleteFaculty,
  exportFaculties,
  importFaculties,
  listFaculties,
  updateFaculty,
} from "../api/faculties";
import { ActionsMenu, type ActionItem } from "../components/ActionsMenu";
import { listUsers } from "../api/users";
import { CARD_STYLE } from "../theme";
import { useAuth } from "../auth/AuthContext";
import { hasPermission } from "../auth/permissions";
import type { FacultyOut, UserOut } from "../types";

export function DepartmentsPage() {
  const { user } = useAuth();
  const canCreate = hasPermission(user, "departments", "create");
  const canEdit = hasPermission(user, "departments", "edit");
  const canDelete = hasPermission(user, "departments", "delete");

  const [departments, setDepartments] = useState<FacultyOut[]>([]);
  const [technicians, setTechnicians] = useState<UserOut[]>([]);
  const [loading, setLoading] = useState(true);

  const [createOpen, setCreateOpen] = useState(false);
  const [renameTarget, setRenameTarget] = useState<FacultyOut | null>(null);
  const [createForm] = Form.useForm();
  const [renameForm] = Form.useForm();
  const [saving, setSaving] = useState(false);

  const [exportLoading, setExportLoading] = useState(false);
  const [importLoading, setImportLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  async function loadData() {
    setLoading(true);
    try {
      const [departmentList, mainTechs, backupTechs] = await Promise.all([
        listFaculties("department", { topLevel: true }),
        listUsers({ role: "technician_main" }),
        listUsers({ role: "technician_backup" }),
      ]);
      setDepartments(departmentList);
      setTechnicians([...mainTechs, ...backupTechs]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function techniciansFor(departmentId: number, role: "technician_main" | "technician_backup") {
    const names = technicians
      .filter((t) => (t.faculty_assignments ?? []).some((a) => a.faculty_id === departmentId && a.role === role))
      .map((t) => t.full_name);
    return names.length > 0 ? names.join(", ") : "-";
  }

  async function handleCreate(values: { name: string }) {
    setSaving(true);
    try {
      await createFaculty(values.name, "department");
      message.success("Bo'lim qo'shildi");
      setCreateOpen(false);
      createForm.resetFields();
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

  async function handleDelete(department: FacultyOut) {
    try {
      await deleteFaculty(department.id);
      message.success("O'chirildi");
      loadData();
    } catch {
      message.error("O'chirib bo'lmadi: bunga bog'liq xodimlar, arizalar yoki inventar mavjud");
    }
  }

  async function handleExport() {
    setExportLoading(true);
    try {
      await exportFaculties("department");
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
      const result = await importFaculties("department", file);
      if (result.skipped.length === 0) {
        message.success(`${result.created} ta bo'lim qo'shildi`);
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
            Yangi bo'lim
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
        dataSource={departments}
        columns={[
          { title: "Nomi", dataIndex: "name" },
          {
            title: "Asosiy texnik xodim",
            key: "main",
            render: (_: unknown, record: FacultyOut) => techniciansFor(record.id, "technician_main"),
          },
          {
            title: "Zaxira texnik xodim",
            key: "backup",
            render: (_: unknown, record: FacultyOut) => techniciansFor(record.id, "technician_backup"),
          },
          ...(canEdit || canDelete
            ? [
                {
                  title: "Amallar",
                  key: "actions",
                  render: (_: unknown, record: FacultyOut) => {
                    const items: ActionItem[] = [];
                    if (canEdit) {
                      items.push({
                        key: "rename",
                        label: "Nomini o'zgartirish",
                        onClick: () => {
                          setRenameTarget(record);
                          renameForm.setFieldsValue({ name: record.name });
                        },
                      });
                    }
                    if (canDelete) {
                      items.push({
                        key: "delete",
                        label: "O'chirish",
                        danger: true,
                        confirmTitle: "O'chirishni tasdiqlaysizmi?",
                        onClick: () => handleDelete(record),
                      });
                    }
                    return <ActionsMenu items={items} />;
                  },
                },
              ]
            : []),
        ]}
      />
      </Card>

      <Modal
        title="Yangi bo'lim"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => createForm.submit()}
        confirmLoading={saving}
        okText="Qo'shish"
        cancelText="Bekor qilish"
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="Bo'lim nomi" rules={[{ required: true }]}>
            <Input />
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
          <Form.Item name="name" label="Bo'lim nomi" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

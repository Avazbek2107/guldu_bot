import { useEffect, useState } from "react";
import { Button, Form, Input, Modal, Select, Space, Table, message } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { assignTechnician, createFaculty, listFaculties, updateFaculty } from "../api/faculties";
import { listUsers } from "../api/users";
import type { FacultyOut, UserOut } from "../types";

export function FacultiesPage() {
  const [faculties, setFaculties] = useState<FacultyOut[]>([]);
  const [technicians, setTechnicians] = useState<UserOut[]>([]);
  const [loading, setLoading] = useState(true);

  const [createOpen, setCreateOpen] = useState(false);
  const [renameTarget, setRenameTarget] = useState<FacultyOut | null>(null);
  const [assignTarget, setAssignTarget] = useState<FacultyOut | null>(null);
  const [createForm] = Form.useForm();
  const [renameForm] = Form.useForm();
  const [assignForm] = Form.useForm();
  const [saving, setSaving] = useState(false);

  async function loadData() {
    setLoading(true);
    try {
      const [facultyList, mainTechs, backupTechs] = await Promise.all([
        listFaculties(),
        listUsers({ role: "technician_main" }),
        listUsers({ role: "technician_backup" }),
      ]);
      setFaculties(facultyList);
      setTechnicians([...mainTechs, ...backupTechs]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function techniciansFor(facultyId: number, role: "technician_main" | "technician_backup") {
    return technicians.find((t) => t.faculty_id === facultyId && t.role === role)?.full_name ?? "-";
  }

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

  async function handleAssign(values: { user_id: number; role: "technician_main" | "technician_backup" }) {
    if (!assignTarget) return;
    setSaving(true);
    try {
      await assignTechnician(assignTarget.id, values.user_id, values.role);
      message.success("Texnik xodim biriktirildi");
      setAssignTarget(null);
      loadData();
    } catch {
      message.error("Xatolik yuz berdi");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          Yangi fakultet
        </Button>
      </Space>

      <Table
        rowKey="id"
        loading={loading}
        dataSource={faculties}
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
          {
            title: "Amallar",
            key: "actions",
            render: (_: unknown, record: FacultyOut) => (
              <Space>
                <Button
                  size="small"
                  onClick={() => {
                    setRenameTarget(record);
                    renameForm.setFieldsValue({ name: record.name });
                  }}
                >
                  Nomini o'zgartirish
                </Button>
                <Button size="small" onClick={() => setAssignTarget(record)}>
                  Texnik xodim biriktirish
                </Button>
              </Space>
            ),
          },
        ]}
      />

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
        title={`Nomini o'zgartirish — ${renameTarget?.name ?? ""}`}
        open={renameTarget !== null}
        onCancel={() => setRenameTarget(null)}
        onOk={() => renameForm.submit()}
        confirmLoading={saving}
        okText="Saqlash"
        cancelText="Bekor qilish"
      >
        <Form form={renameForm} layout="vertical" onFinish={handleRename}>
          <Form.Item name="name" label="Fakultet nomi" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`Texnik xodim biriktirish — ${assignTarget?.name ?? ""}`}
        open={assignTarget !== null}
        onCancel={() => setAssignTarget(null)}
        onOk={() => assignForm.submit()}
        confirmLoading={saving}
        okText="Biriktirish"
        cancelText="Bekor qilish"
      >
        <Form form={assignForm} layout="vertical" onFinish={handleAssign}>
          <Form.Item name="user_id" label="Texnik xodim" rules={[{ required: true }]}>
            <Select
              placeholder="Texnik xodimni tanlang"
              options={technicians.map((t) => ({ value: t.id, label: `${t.full_name} (hozirgi fakultet: ${t.faculty_id ?? "-"})` }))}
            />
          </Form.Item>
          <Form.Item name="role" label="Lavozimi" rules={[{ required: true }]}>
            <Select
              options={[
                { value: "technician_main", label: "Asosiy texnik xodim" },
                { value: "technician_backup", label: "Zaxira texnik xodim" },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

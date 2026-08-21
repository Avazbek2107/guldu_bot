import { useEffect, useState } from "react";
import { Button, Card, Form, Input, Modal, Select, Space, Table, Tag, message } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { createProject, deleteProject, listProjects, updateProject, type ProjectPayload } from "../api/projects";
import { extractErrorDetail } from "../api/client";
import { ActionsMenu } from "../components/ActionsMenu";
import { CARD_STYLE } from "../theme";
import { useAuth } from "../auth/AuthContext";
import { hasPermission } from "../auth/permissions";
import { PROJECT_STATUS_OPTIONS, type ProjectOut } from "../types";

const STATUS_OPTIONS = PROJECT_STATUS_OPTIONS.map((v) => ({ value: v, label: v }));

const STATUS_COLORS: Record<string, string> = {
  Rejalashtirilgan: "default",
  Jarayonda: "blue",
  Yakunlangan: "green",
  "To'xtatilgan": "red",
};

export function ProjectsPage() {
  const { user } = useAuth();
  const canCreate = hasPermission(user, "projects", "create");
  const canEdit = hasPermission(user, "projects", "edit");
  const canDelete = hasPermission(user, "projects", "delete");

  const [projects, setProjects] = useState<ProjectOut[]>([]);
  const [loading, setLoading] = useState(true);

  const [createOpen, setCreateOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<ProjectOut | null>(null);
  const [createForm] = Form.useForm<ProjectPayload>();
  const [editForm] = Form.useForm<ProjectPayload>();
  const [saving, setSaving] = useState(false);

  async function loadData() {
    setLoading(true);
    try {
      setProjects(await listProjects());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleCreate(values: ProjectPayload) {
    setSaving(true);
    try {
      await createProject(values);
      message.success("Loyiha qo'shildi");
      setCreateOpen(false);
      createForm.resetFields();
      loadData();
    } catch (err) {
      message.error(extractErrorDetail(err) ?? "Xatolik yuz berdi");
    } finally {
      setSaving(false);
    }
  }

  async function handleEditSave(values: ProjectPayload) {
    if (!editTarget) return;
    setSaving(true);
    try {
      await updateProject(editTarget.id, values);
      message.success("Saqlandi");
      setEditTarget(null);
      loadData();
    } catch (err) {
      message.error(extractErrorDetail(err) ?? "Xatolik yuz berdi");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(project: ProjectOut) {
    try {
      await deleteProject(project.id);
      message.success("O'chirildi");
      loadData();
    } catch (err) {
      message.error(extractErrorDetail(err) ?? "Xatolik yuz berdi");
    }
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }} wrap>
        {canCreate && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
            Yangi loyiha
          </Button>
        )}
      </Space>

      <Card style={CARD_STYLE}>
        <Table
          rowKey="id"
          loading={loading}
          scroll={{ x: "max-content" }}
          dataSource={projects}
          columns={[
            { title: "Nomi", dataIndex: "name" },
            { title: "Tavsifi", dataIndex: "description", render: (v: string | null) => v ?? "-" },
            {
              title: "Holati",
              dataIndex: "status",
              render: (v: string) => <Tag color={STATUS_COLORS[v] ?? "default"}>{v}</Tag>,
            },
            { title: "Mas'ul", dataIndex: "responsible_person", render: (v: string | null) => v ?? "-" },
            ...(canEdit || canDelete
              ? [
                  {
                    title: "Amallar",
                    key: "actions",
                    fixed: "right" as const,
                    width: 72,
                    render: (_: unknown, record: ProjectOut) => (
                      <ActionsMenu
                        items={[
                          ...(canEdit
                            ? [
                                {
                                  key: "edit",
                                  label: "Tahrirlash",
                                  onClick: () => {
                                    setEditTarget(record);
                                    editForm.setFieldsValue({
                                      name: record.name,
                                      description: record.description ?? undefined,
                                      status: record.status,
                                      responsible_person: record.responsible_person ?? undefined,
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
                ]
              : []),
          ]}
        />
      </Card>

      <Modal
        title="Yangi loyiha"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => createForm.submit()}
        confirmLoading={saving}
        okText="Qo'shish"
        cancelText="Bekor qilish"
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreate} initialValues={{ status: "Rejalashtirilgan" }}>
          <Form.Item name="name" label="Loyiha nomi" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Tavsifi">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="status" label="Holati">
            <Select options={STATUS_OPTIONS} />
          </Form.Item>
          <Form.Item name="responsible_person" label="Mas'ul shaxs">
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`Tahrirlash — ${editTarget?.name ?? ""}`}
        open={editTarget !== null}
        onCancel={() => setEditTarget(null)}
        onOk={() => editForm.submit()}
        confirmLoading={saving}
        okText="Saqlash"
        cancelText="Bekor qilish"
      >
        <Form form={editForm} layout="vertical" onFinish={handleEditSave}>
          <Form.Item name="name" label="Loyiha nomi" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Tavsifi">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="status" label="Holati">
            <Select options={STATUS_OPTIONS} />
          </Form.Item>
          <Form.Item name="responsible_person" label="Mas'ul shaxs">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

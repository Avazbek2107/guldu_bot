import { useEffect, useState } from "react";
import { Button, Card, Form, Input, InputNumber, Modal, Space, Table, Tag, message } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { ActionsMenu } from "../components/ActionsMenu";
import { PermissionMatrix, type PermissionsValue } from "../components/PermissionMatrix";
import { CARD_STYLE } from "../theme";
import { blockUser, createUser, deleteUser, listUsers, unblockUser, updateUser } from "../api/users";
import { useAuth } from "../auth/AuthContext";
import { PERMISSION_RESOURCE_LABELS_UZ, type PermissionResource, type UserOut } from "../types";

interface CreateFormValues {
  full_name: string;
  phone: string;
  username: string;
  password: string;
  permissions?: PermissionsValue;
  telegram_id?: number;
}

interface EditFormValues {
  full_name: string;
  phone: string;
  password?: string;
  telegram_id?: number;
  permissions?: PermissionsValue;
}

function permissionsSummary(permissions: UserOut["permissions"]): string {
  const resources = Object.keys(permissions ?? {}).filter(
    (r) => (permissions?.[r as PermissionResource]?.length ?? 0) > 0,
  ) as PermissionResource[];
  if (resources.length === 0) return "Ruxsat berilmagan";
  return resources.map((r) => PERMISSION_RESOURCE_LABELS_UZ[r]).join(", ");
}

export function AdminsPage() {
  const { user: currentUser } = useAuth();
  const isSuperAdminUser = currentUser?.role === "super_admin";
  // Only a Super Admin may create/edit/block/delete Admin accounts — this
  // mirrors a backend safeguard (_can_manage_target_role) that always
  // rejects such changes from a fellow Admin, so the controls are hidden
  // rather than shown-then-403'd.
  const canManage = isSuperAdminUser;

  const [admins, setAdmins] = useState<UserOut[]>([]);
  const [loading, setLoading] = useState(true);

  const [createOpen, setCreateOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<UserOut | null>(null);
  const [createForm] = Form.useForm<CreateFormValues>();
  const [editForm] = Form.useForm<EditFormValues>();
  const [saving, setSaving] = useState(false);

  async function loadAdmins() {
    setLoading(true);
    try {
      setAdmins(await listUsers({ role: "admin" }));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAdmins();
  }, []);

  async function handleCreate(values: CreateFormValues) {
    setSaving(true);
    try {
      await createUser({
        username: values.username,
        password: values.password,
        full_name: values.full_name,
        phone: values.phone,
        role: "admin",
        faculty_assignments: [],
        permissions: values.permissions ?? {},
        telegram_id: values.telegram_id ?? null,
      });
      message.success("Admin yaratildi");
      setCreateOpen(false);
      createForm.resetFields();
      loadAdmins();
    } catch {
      message.error("Xatolik: username band bo'lishi mumkin");
    } finally {
      setSaving(false);
    }
  }

  async function handleEditSave(values: EditFormValues) {
    if (!editTarget) return;
    setSaving(true);
    try {
      await updateUser(editTarget.id, {
        full_name: values.full_name,
        phone: values.phone,
        password: values.password || undefined,
        telegram_id: values.telegram_id ?? null,
        permissions: values.permissions ?? {},
      });
      message.success("Saqlandi");
      setEditTarget(null);
      loadAdmins();
    } catch {
      message.error("Xatolik yuz berdi");
    } finally {
      setSaving(false);
    }
  }

  async function handleToggleBlock(admin: UserOut) {
    try {
      if (admin.is_blocked) {
        await unblockUser(admin.id);
        message.success("Blokdan chiqarildi");
      } else {
        await blockUser(admin.id);
        message.success("Bloklandi");
      }
      loadAdmins();
    } catch {
      message.error("Xatolik yuz berdi");
    }
  }

  async function handleDelete(admin: UserOut) {
    try {
      await deleteUser(admin.id);
      message.success("O'chirildi");
      loadAdmins();
    } catch {
      message.error("Bu adminni o'chirib bo'lmadi.");
    }
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }} wrap>
        {canManage && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
            Yangi admin
          </Button>
        )}
      </Space>

      <Card style={CARD_STYLE}>
        <Table
          rowKey="id"
          loading={loading}
          scroll={{ x: "max-content" }}
          dataSource={admins}
          columns={[
            { title: "FISH", dataIndex: "full_name" },
            { title: "Login", dataIndex: "username", render: (v: string | null) => v ?? "-" },
            { title: "Telefon", dataIndex: "phone" },
            {
              title: "Ruxsatlar",
              key: "permissions",
              render: (_: unknown, record: UserOut) => permissionsSummary(record.permissions),
            },
            {
              title: "Telegram",
              dataIndex: "telegram_id",
              render: (v: number | null) => (
                <div
                  style={{
                    background: v != null ? "#e6f7e6" : "#fdecec",
                    borderRadius: 6,
                    padding: "4px 10px",
                    textAlign: "center",
                  }}
                >
                  {v != null ? "Bog'langan" : "Bog'lanmagan"}
                </div>
              ),
            },
            {
              title: "Holat",
              key: "status",
              render: (_: unknown, record: UserOut) => (
                <Space>
                  {record.is_blocked && <Tag color="red">Bloklangan</Tag>}
                  {!record.is_blocked && <Tag color="green">Faol</Tag>}
                </Space>
              ),
            },
            ...(canManage
              ? [
                  {
                    title: "Amallar",
                    key: "actions",
                    fixed: "right" as const,
                    width: 72,
                    render: (_: unknown, record: UserOut) => (
                      <ActionsMenu
                        items={[
                          {
                            key: "edit",
                            label: "Tahrirlash",
                            onClick: () => {
                              setEditTarget(record);
                              editForm.setFieldsValue({
                                full_name: record.full_name,
                                phone: record.phone,
                                telegram_id: record.telegram_id ?? undefined,
                                permissions: record.permissions ?? {},
                              });
                            },
                          },
                          {
                            key: "block",
                            label: record.is_blocked ? "Blokdan chiqarish" : "Bloklash",
                            onClick: () => handleToggleBlock(record),
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
                ]
              : []),
          ]}
        />
      </Card>

      <Modal
        title="Yangi admin"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => createForm.submit()}
        confirmLoading={saving}
        okText="Yaratish"
        cancelText="Bekor qilish"
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="full_name" label="FISH" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="Telefon" rules={[{ required: true }]}>
            <Input placeholder="+998901234567" />
          </Form.Item>
          <Form.Item
            name="username"
            label="Login"
            rules={[
              { required: true, message: "Loginni kiriting" },
              { min: 3, message: "Login kamida 3 belgidan iborat bo'lishi kerak" },
            ]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="password"
            label="Parol"
            rules={[
              { required: true, message: "Parolni kiriting" },
              { min: 8, message: "Parol kamida 8 belgidan iborat bo'lishi kerak" },
            ]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item name="permissions" label="Ruxsatlar">
            <PermissionMatrix />
          </Form.Item>
          <Form.Item
            name="telegram_id"
            label="Telegram ID (ixtiyoriy)"
            extra="Botga @userinfobot orqali adminning Telegram ID'sini bilib oling."
          >
            <InputNumber style={{ width: "100%" }} placeholder="Masalan: 123456789" controls={false} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`Tahrirlash — ${editTarget?.full_name ?? ""}`}
        open={editTarget !== null}
        onCancel={() => setEditTarget(null)}
        onOk={() => editForm.submit()}
        confirmLoading={saving}
        okText="Saqlash"
        cancelText="Bekor qilish"
      >
        <Form form={editForm} layout="vertical" onFinish={handleEditSave}>
          <Form.Item name="full_name" label="FISH" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="Telefon" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="permissions" label="Ruxsatlar">
            <PermissionMatrix />
          </Form.Item>
          <Form.Item
            name="telegram_id"
            label="Telegram ID (ixtiyoriy)"
            extra="Botga @userinfobot orqali adminning Telegram ID'sini bilib oling."
          >
            <InputNumber style={{ width: "100%" }} placeholder="Masalan: 123456789" controls={false} />
          </Form.Item>
          <Form.Item
            name="password"
            label="Yangi parol (ixtiyoriy)"
            rules={[{ min: 8, message: "Parol kamida 8 belgidan iborat bo'lishi kerak" }]}
          >
            <Input.Password placeholder="O'zgartirish uchun kiriting" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

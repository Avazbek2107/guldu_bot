import { useEffect, useState } from "react";
import { Button, Form, Input, InputNumber, Modal, Popconfirm, Select, Space, Table, Tag, message } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import {
  blockUser,
  createUser,
  deleteUser,
  listUsers,
  unblockUser,
  updateUser,
  type UserCreatePayload,
} from "../api/users";
import { listFaculties } from "../api/faculties";
import { ROLE_LABELS_UZ, type FacultyOut, type UserOut, type UserRole } from "../types";

const CREATABLE_ROLES: UserRole[] = ["technician_main", "technician_backup", "super_admin"];

export function UsersPage() {
  const [users, setUsers] = useState<UserOut[]>([]);
  const [faculties, setFaculties] = useState<FacultyOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [roleFilter, setRoleFilter] = useState<UserRole | undefined>();

  const [createOpen, setCreateOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<UserOut | null>(null);
  const [createForm] = Form.useForm<UserCreatePayload>();
  const [editForm] = Form.useForm();
  const [saving, setSaving] = useState(false);

  const facultyName = (id: number | null) => faculties.find((f) => f.id === id)?.name ?? "-";

  async function loadUsers() {
    setLoading(true);
    try {
      setUsers(await listUsers(roleFilter ? { role: roleFilter } : undefined));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    listFaculties().then(setFaculties);
  }, []);

  useEffect(() => {
    loadUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roleFilter]);

  async function handleCreate(values: UserCreatePayload) {
    setSaving(true);
    try {
      await createUser(values);
      message.success("Foydalanuvchi yaratildi");
      setCreateOpen(false);
      createForm.resetFields();
      loadUsers();
    } catch {
      message.error("Xatolik: username band yoki fakultetda asosiy texnik xodim allaqachon bor");
    } finally {
      setSaving(false);
    }
  }

  async function handleEditSave(values: {
    full_name: string;
    phone: string;
    faculty_id?: number;
    password?: string;
    telegram_id?: number;
  }) {
    if (!editTarget) return;
    setSaving(true);
    try {
      await updateUser(editTarget.id, {
        full_name: values.full_name,
        phone: values.phone,
        faculty_id: values.faculty_id ?? null,
        password: values.password || undefined,
        telegram_id: values.telegram_id ?? null,
      });
      message.success("Saqlandi");
      setEditTarget(null);
      loadUsers();
    } catch {
      message.error("Xatolik yuz berdi");
    } finally {
      setSaving(false);
    }
  }

  async function handleToggleBlock(user: UserOut) {
    try {
      if (user.is_blocked) {
        await unblockUser(user.id);
        message.success("Blokdan chiqarildi");
      } else {
        await blockUser(user.id);
        message.success("Bloklandi");
      }
      loadUsers();
    } catch {
      message.error("Xatolik yuz berdi");
    }
  }

  async function handleDelete(user: UserOut) {
    try {
      await deleteUser(user.id);
      message.success("O'chirildi");
      loadUsers();
    } catch {
      message.error("Bu foydalanuvchi bildirishnomalarga bog'langan, o'chirib bo'lmaydi. Bloklang.");
    }
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Select
          allowClear
          placeholder="Rol bo'yicha filtrlash"
          style={{ width: 220 }}
          value={roleFilter}
          onChange={setRoleFilter}
          options={Object.entries(ROLE_LABELS_UZ).map(([value, label]) => ({ value, label }))}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          Yangi foydalanuvchi
        </Button>
      </Space>

      <Table
        rowKey="id"
        loading={loading}
        dataSource={users}
        columns={[
          { title: "FISH", dataIndex: "full_name" },
          { title: "Login", dataIndex: "username", render: (v: string | null) => v ?? "-" },
          { title: "Telefon", dataIndex: "phone" },
          { title: "Rol", dataIndex: "role", render: (v: UserRole) => ROLE_LABELS_UZ[v] },
          { title: "Fakultet", dataIndex: "faculty_id", render: (v: number | null) => facultyName(v) },
          {
            title: "Telegram",
            dataIndex: "telegram_id",
            render: (v: number | null) =>
              v != null ? <Tag color="blue">Bog'langan ({v})</Tag> : <Tag>Bog'lanmagan</Tag>,
          },
          {
            title: "Holat",
            key: "status",
            render: (_: unknown, record: UserOut) => (
              <Space>
                {record.is_blocked && <Tag color="red">Bloklangan</Tag>}
                {record.is_suspicious && <Tag color="orange">Shubhali</Tag>}
                {!record.is_blocked && !record.is_suspicious && <Tag color="green">Faol</Tag>}
              </Space>
            ),
          },
          {
            title: "Amallar",
            key: "actions",
            render: (_: unknown, record: UserOut) => (
              <Space>
                <Button
                  size="small"
                  onClick={() => {
                    setEditTarget(record);
                    editForm.setFieldsValue({
                      full_name: record.full_name,
                      phone: record.phone,
                      faculty_id: record.faculty_id ?? undefined,
                      telegram_id: record.telegram_id ?? undefined,
                    });
                  }}
                >
                  Tahrirlash
                </Button>
                <Button size="small" onClick={() => handleToggleBlock(record)}>
                  {record.is_blocked ? "Blokdan chiqarish" : "Bloklash"}
                </Button>
                <Popconfirm title="O'chirishni tasdiqlaysizmi?" onConfirm={() => handleDelete(record)}>
                  <Button size="small" danger>
                    O'chirish
                  </Button>
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      <Modal
        title="Yangi foydalanuvchi"
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
          <Form.Item name="role" label="Rol" rules={[{ required: true }]}>
            <Select options={CREATABLE_ROLES.map((r) => ({ value: r, label: ROLE_LABELS_UZ[r] }))} />
          </Form.Item>
          <Form.Item name="faculty_id" label="Fakultet">
            <Select
              allowClear
              placeholder="Super Admin uchun bo'sh qoldiring"
              options={faculties.map((f) => ({ value: f.id, label: f.name }))}
            />
          </Form.Item>
          <Form.Item
            name="telegram_id"
            label="Telegram ID (ixtiyoriy)"
            extra="Botga @userinfobot orqali xodimning Telegram ID'sini bilib oling. Bo'sh qoldirsangiz, xodim botda /start bosib telefon raqamini ulashganda avtomatik bog'lanadi."
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
          <Form.Item name="faculty_id" label="Fakultet">
            <Select allowClear options={faculties.map((f) => ({ value: f.id, label: f.name }))} />
          </Form.Item>
          <Form.Item
            name="telegram_id"
            label="Telegram ID (ixtiyoriy)"
            extra="Botga @userinfobot orqali xodimning Telegram ID'sini bilib oling."
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

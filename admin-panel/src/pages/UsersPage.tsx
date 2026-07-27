import { useEffect, useState } from "react";
import { Button, Card, Form, Input, InputNumber, Modal, Select, Space, Table, Tag, message } from "antd";
import { MinusCircleOutlined, PlusOutlined } from "@ant-design/icons";
import { ActionsMenu } from "../components/ActionsMenu";
import { CARD_STYLE } from "../theme";
import {
  blockUser,
  createUser,
  deleteUser,
  listUsers,
  unblockUser,
  updateUser,
  type FacultyAssignmentInput,
} from "../api/users";
import { listFaculties } from "../api/faculties";
import {
  orgUnitLabel,
  ROLE_LABELS_UZ,
  type FacultyOut,
  type TechnicianRole,
  type UserOut,
  type UserRole,
} from "../types";

const EMPLOYEE_ROLES: UserRole[] = ["technician_main", "technician_backup", "super_admin"];
const TECHNICIAN_ROLES: UserRole[] = ["technician_main", "technician_backup"];

type UiRole = "technician" | "super_admin";

const UI_ROLE_OPTIONS: { value: UiRole; label: string }[] = [
  { value: "technician", label: "Texnik xodim" },
  { value: "super_admin", label: "Super Admin" },
];

const FACULTY_ROLE_OPTIONS: { value: TechnicianRole; label: string }[] = [
  { value: "technician_main", label: "Asosiy" },
  { value: "technician_backup", label: "Zaxira" },
];

function resolveTechnicianRole(assignments: FacultyAssignmentInput[]): UserRole {
  return assignments.some((a) => a.role === "technician_main") ? "technician_main" : "technician_backup";
}

interface CreateFormValues {
  full_name: string;
  phone: string;
  username: string;
  password: string;
  uiRole: UiRole;
  faculty_assignments?: FacultyAssignmentInput[];
  telegram_id?: number;
}

interface EditFormValues {
  full_name: string;
  phone: string;
  password?: string;
  telegram_id?: number;
  faculty_assignments?: FacultyAssignmentInput[];
}

function FacultyAssignmentsList({ faculties }: { faculties: FacultyOut[] }) {
  return (
    <Form.List
      name="faculty_assignments"
      rules={[
        {
          validator: async (_, assignments: FacultyAssignmentInput[] | undefined) => {
            if (!assignments || assignments.length === 0) {
              return Promise.reject(new Error("Kamida bitta fakultet tanlang"));
            }
          },
        },
      ]}
    >
      {(fields, { add, remove }, { errors }) => (
        <>
          {fields.map((field) => (
            <Space key={field.key} align="baseline" wrap style={{ display: "flex", width: "100%", marginBottom: 8 }}>
              <Form.Item
                name={[field.name, "faculty_id"]}
                rules={[{ required: true, message: "Fakultetni tanlang" }]}
                style={{ marginBottom: 0, flex: "1 1 160px" }}
              >
                <Select
                  placeholder="Fakultet"
                  style={{ width: "100%", minWidth: 140 }}
                  options={faculties.map((f) => ({ value: f.id, label: orgUnitLabel(f) }))}
                />
              </Form.Item>
              <Form.Item
                name={[field.name, "role"]}
                rules={[{ required: true, message: "Lavozimni tanlang" }]}
                initialValue="technician_backup"
                style={{ marginBottom: 0, flex: "1 1 120px" }}
              >
                <Select style={{ width: "100%", minWidth: 110 }} options={FACULTY_ROLE_OPTIONS} />
              </Form.Item>
              <MinusCircleOutlined onClick={() => remove(field.name)} />
            </Space>
          ))}
          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
              Fakultet qo'shish
            </Button>
            <Form.ErrorList errors={errors} />
          </Form.Item>
        </>
      )}
    </Form.List>
  );
}

export function UsersPage() {
  const [users, setUsers] = useState<UserOut[]>([]);
  const [faculties, setFaculties] = useState<FacultyOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [roleFilter, setRoleFilter] = useState<UserRole | undefined>();

  const [createOpen, setCreateOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<UserOut | null>(null);
  const [createForm] = Form.useForm<CreateFormValues>();
  const [editForm] = Form.useForm<EditFormValues>();
  const [saving, setSaving] = useState(false);

  async function loadUsers() {
    setLoading(true);
    try {
      setUsers(await listUsers({ role: roleFilter ? [roleFilter] : EMPLOYEE_ROLES }));
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

  async function handleCreate(values: CreateFormValues) {
    setSaving(true);
    try {
      const assignments = values.uiRole === "technician" ? values.faculty_assignments ?? [] : [];
      await createUser({
        username: values.username,
        password: values.password,
        full_name: values.full_name,
        phone: values.phone,
        role: values.uiRole === "super_admin" ? "super_admin" : resolveTechnicianRole(assignments),
        faculty_assignments: assignments,
        telegram_id: values.telegram_id ?? null,
      });
      message.success("Xodim yaratildi");
      setCreateOpen(false);
      createForm.resetFields();
      loadUsers();
    } catch {
      message.error("Xatolik: username band yoki fakultetda asosiy texnik xodim allaqachon bor");
    } finally {
      setSaving(false);
    }
  }

  async function handleEditSave(values: EditFormValues) {
    if (!editTarget) return;
    const isTechnician = TECHNICIAN_ROLES.includes(editTarget.role);
    setSaving(true);
    try {
      await updateUser(editTarget.id, {
        full_name: values.full_name,
        phone: values.phone,
        password: values.password || undefined,
        telegram_id: values.telegram_id ?? null,
        ...(isTechnician ? { faculty_assignments: values.faculty_assignments ?? [] } : {}),
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
      message.error("Bu xodim bildirishnomalarga bog'langan, o'chirib bo'lmaydi. Bloklang.");
    }
  }

  const editTargetIsTechnician = editTarget != null && TECHNICIAN_ROLES.includes(editTarget.role);

  return (
    <div>
      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          allowClear
          placeholder="Rol bo'yicha filtrlash"
          style={{ width: 220 }}
          value={roleFilter}
          onChange={setRoleFilter}
          options={EMPLOYEE_ROLES.map((r) => ({ value: r, label: ROLE_LABELS_UZ[r] }))}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          Yangi xodim
        </Button>
      </Space>

      <Card style={CARD_STYLE}>
      <Table
        rowKey="id"
        loading={loading}
        scroll={{ x: "max-content" }}
        dataSource={users}
        columns={[
          { title: "FISH", dataIndex: "full_name" },
          { title: "Login", dataIndex: "username", render: (v: string | null) => v ?? "-" },
          { title: "Telefon", dataIndex: "phone" },
          { title: "Rol", dataIndex: "role", render: (v: UserRole) => ROLE_LABELS_UZ[v] },
          {
            title: "Biriktirilgan hudud",
            key: "faculties",
            render: (_: unknown, record: UserOut) => {
              const assignments = [...(record.faculty_assignments ?? [])].sort((a, b) =>
                a.role === b.role ? 0 : a.role === "technician_main" ? -1 : 1,
              );
              if (assignments.length === 0) return "-";
              return (
                <Space orientation="vertical" size={4}>
                  {assignments.map((a) => (
                    <Tag key={a.faculty_id} color={a.role === "technician_main" ? "gold" : "default"}>
                      {a.faculty_name} — {a.role === "technician_main" ? "asosiy" : "zaxira"}
                    </Tag>
                  ))}
                </Space>
              );
            },
          },
          {
            title: "Telegram",
            dataIndex: "telegram_id",
            onCell: (record: UserOut) => ({
              style: { background: record.telegram_id != null ? "#e6f7e6" : "#fdecec" },
            }),
            render: (v: number | null) => (v != null ? "Bog'langan" : "Bog'lanmagan"),
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
            fixed: "right",
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
                        faculty_assignments: (record.faculty_assignments ?? []).map((a) => ({
                          faculty_id: a.faculty_id,
                          role: a.role,
                        })),
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
        ]}
      />
      </Card>

      <Modal
        title="Yangi xodim"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => createForm.submit()}
        confirmLoading={saving}
        okText="Yaratish"
        cancelText="Bekor qilish"
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreate} initialValues={{ uiRole: "technician" }}>
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
          <Form.Item name="uiRole" label="Rol" rules={[{ required: true }]}>
            <Select options={UI_ROLE_OPTIONS} />
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prev: CreateFormValues, cur: CreateFormValues) => prev.uiRole !== cur.uiRole}
          >
            {({ getFieldValue }) =>
              getFieldValue("uiRole") === "technician" ? (
                <Form.Item label="Fakultet biriktirishlar">
                  <FacultyAssignmentsList faculties={faculties} />
                </Form.Item>
              ) : null
            }
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
          {editTargetIsTechnician && (
            <Form.Item label="Fakultet biriktirishlar">
              <FacultyAssignmentsList faculties={faculties} />
            </Form.Item>
          )}
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

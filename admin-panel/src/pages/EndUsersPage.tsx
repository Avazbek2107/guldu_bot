import { useEffect, useState } from "react";
import { Button, Form, Input, InputNumber, Modal, Popconfirm, Select, Space, Table, Tag, message } from "antd";
import { blockUser, deleteUser, listUsers, unblockUser, updateUser } from "../api/users";
import { listFaculties } from "../api/faculties";
import type { FacultyOut, UserOut } from "../types";

export function EndUsersPage() {
  const [users, setUsers] = useState<UserOut[]>([]);
  const [faculties, setFaculties] = useState<FacultyOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [facultyFilter, setFacultyFilter] = useState<number | undefined>();

  const [editTarget, setEditTarget] = useState<UserOut | null>(null);
  const [editForm] = Form.useForm();
  const [saving, setSaving] = useState(false);

  const facultyName = (id: number | null) => faculties.find((f) => f.id === id)?.name ?? "-";

  async function loadUsers() {
    setLoading(true);
    try {
      setUsers(await listUsers({ role: "faculty_staff", faculty_id: facultyFilter }));
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
  }, [facultyFilter]);

  async function handleEditSave(values: { full_name: string; phone: string; faculty_id?: number; telegram_id?: number }) {
    if (!editTarget) return;
    setSaving(true);
    try {
      await updateUser(editTarget.id, {
        full_name: values.full_name,
        phone: values.phone,
        faculty_id: values.faculty_id ?? null,
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
      message.error("Bu foydalanuvchi arizalarga bog'langan, o'chirib bo'lmaydi. Bloklang.");
    }
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Select
          allowClear
          placeholder="Fakultet bo'yicha filtrlash"
          style={{ width: 240 }}
          value={facultyFilter}
          onChange={setFacultyFilter}
          options={faculties.map((f) => ({ value: f.id, label: f.name }))}
        />
      </Space>

      <Table
        rowKey="id"
        loading={loading}
        dataSource={users}
        columns={[
          { title: "FISH", dataIndex: "full_name" },
          { title: "Telefon", dataIndex: "phone" },
          { title: "Fakultet", dataIndex: "faculty_id", render: (v: number | null) => facultyName(v) },
          {
            title: "Telegram",
            dataIndex: "telegram_id",
            render: (v: number | null) =>
              v != null ? <Tag color="blue">Bog'langan</Tag> : <Tag>Bog'lanmagan</Tag>,
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
            extra="Botga @userinfobot orqali foydalanuvchining Telegram ID'sini bilib oling."
          >
            <InputNumber style={{ width: "100%" }} placeholder="Masalan: 123456789" controls={false} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

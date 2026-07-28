import { useEffect, useRef, useState } from "react";
import { Card, Form, Input, InputNumber, Modal, Select, Space, Table, Tag, message } from "antd";
import { blockUser, deleteUser, listUsers, unblockUser, updateUser } from "../api/users";
import { listFaculties } from "../api/faculties";
import { ActionsMenu } from "../components/ActionsMenu";
import { CARD_STYLE } from "../theme";
import { useAuth } from "../auth/AuthContext";
import { hasPermission } from "../auth/permissions";
import { orgUnitLabel, type FacultyOut, type UserOut } from "../types";

export function EndUsersPage() {
  const { user: currentUser } = useAuth();
  const canEdit = hasPermission(currentUser, "end_users", "edit");
  const canDelete = hasPermission(currentUser, "end_users", "delete");

  const [users, setUsers] = useState<UserOut[]>([]);
  const [faculties, setFaculties] = useState<FacultyOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [facultyFilter, setFacultyFilter] = useState<number | undefined>();

  const [editTarget, setEditTarget] = useState<UserOut | null>(null);
  const [editForm] = Form.useForm();
  const [saving, setSaving] = useState(false);

  const facultyName = (id: number | null) => faculties.find((f) => f.id === id)?.name ?? "-";
  const requestIdRef = useRef(0);

  async function loadUsers() {
    const requestId = ++requestIdRef.current;
    setLoading(true);
    try {
      const data = await listUsers({ role: "faculty_staff", faculty_id: facultyFilter });
      if (requestId === requestIdRef.current) {
        setUsers(data);
      }
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
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
      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          allowClear
          placeholder="Fakultet bo'yicha filtrlash"
          style={{ width: 240 }}
          value={facultyFilter}
          onChange={setFacultyFilter}
          options={faculties.map((f) => ({ value: f.id, label: orgUnitLabel(f) }))}
        />
      </Space>

      <Card style={CARD_STYLE}>
      <Table
        rowKey="id"
        scroll={{ x: "max-content" }}
        loading={loading}
        dataSource={users}
        columns={[
          { title: "FISH", dataIndex: "full_name" },
          { title: "Telefon", dataIndex: "phone" },
          { title: "Fakultet", dataIndex: "faculty_id", render: (v: number | null) => facultyName(v) },
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
            render: (_: unknown, record: UserOut) =>
              !canEdit && !canDelete ? null : (
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
                              full_name: record.full_name,
                              phone: record.phone,
                              faculty_id: record.faculty_id ?? undefined,
                              telegram_id: record.telegram_id ?? undefined,
                            });
                          },
                        },
                      ]
                    : []),
                  ...(canEdit
                    ? [
                        {
                          key: "block",
                          label: record.is_blocked ? "Blokdan chiqarish" : "Bloklash",
                          onClick: () => handleToggleBlock(record),
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
            <Select allowClear options={faculties.map((f) => ({ value: f.id, label: orgUnitLabel(f) }))} />
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

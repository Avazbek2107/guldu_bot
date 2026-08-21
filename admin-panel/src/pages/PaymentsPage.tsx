import { useEffect, useState } from "react";
import { Button, Card, DatePicker, Form, Input, InputNumber, Modal, Select, Space, Table, Tag, message } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import dayjs, { type Dayjs } from "dayjs";
import {
  createServicePayment,
  deleteServicePayment,
  listServicePayments,
  updateServicePayment,
  type ServicePaymentPayload,
} from "../api/servicePayments";
import { extractErrorDetail } from "../api/client";
import { ActionsMenu } from "../components/ActionsMenu";
import { CARD_STYLE } from "../theme";
import { useAuth } from "../auth/AuthContext";
import { hasPermission } from "../auth/permissions";
import { PAYMENT_CATEGORY_OPTIONS, type ServicePaymentOut } from "../types";

const CATEGORY_OPTIONS = PAYMENT_CATEGORY_OPTIONS.map((v) => ({ value: v, label: v }));

const STATUS_COLORS: Record<string, string> = {
  Faol: "green",
  "Tez orada": "orange",
  "Muddati o'tgan": "red",
};

interface FormValues {
  name: string;
  category: string;
  amount?: number | null;
  due_date: Dayjs;
  responsible_person?: string;
  notes?: string;
}

export function PaymentsPage() {
  const { user } = useAuth();
  const canCreate = hasPermission(user, "payments", "create");
  const canEdit = hasPermission(user, "payments", "edit");
  const canDelete = hasPermission(user, "payments", "delete");

  const [payments, setPayments] = useState<ServicePaymentOut[]>([]);
  const [loading, setLoading] = useState(true);

  const [createOpen, setCreateOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<ServicePaymentOut | null>(null);
  const [createForm] = Form.useForm<FormValues>();
  const [editForm] = Form.useForm<FormValues>();
  const [saving, setSaving] = useState(false);

  async function loadData() {
    setLoading(true);
    try {
      setPayments(await listServicePayments());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function toPayload(values: FormValues): ServicePaymentPayload {
    return {
      name: values.name,
      category: values.category,
      amount: values.amount ?? null,
      due_date: values.due_date.format("YYYY-MM-DD"),
      responsible_person: values.responsible_person || null,
      notes: values.notes || null,
    };
  }

  async function handleCreate(values: FormValues) {
    setSaving(true);
    try {
      await createServicePayment(toPayload(values));
      message.success("Qo'shildi");
      setCreateOpen(false);
      createForm.resetFields();
      loadData();
    } catch (err) {
      message.error(extractErrorDetail(err) ?? "Xatolik yuz berdi");
    } finally {
      setSaving(false);
    }
  }

  async function handleEditSave(values: FormValues) {
    if (!editTarget) return;
    setSaving(true);
    try {
      await updateServicePayment(editTarget.id, toPayload(values));
      message.success("Saqlandi");
      setEditTarget(null);
      loadData();
    } catch (err) {
      message.error(extractErrorDetail(err) ?? "Xatolik yuz berdi");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(payment: ServicePaymentOut) {
    try {
      await deleteServicePayment(payment.id);
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
            Yangi to'lov
          </Button>
        )}
      </Space>

      <Card style={CARD_STYLE}>
        <Table
          rowKey="id"
          loading={loading}
          scroll={{ x: "max-content" }}
          dataSource={payments}
          columns={[
            { title: "Nomi", dataIndex: "name" },
            { title: "Turi", dataIndex: "category" },
            {
              title: "Summasi",
              dataIndex: "amount",
              render: (v: number | null) => (v != null ? v.toLocaleString("uz-UZ") : "-"),
            },
            { title: "Muddati", dataIndex: "due_date" },
            {
              title: "Holati",
              dataIndex: "status",
              render: (v: string, record: ServicePaymentOut) => (
                <Tag color={STATUS_COLORS[v] ?? "default"}>
                  {v}
                  {v !== "Faol" && (record.days_left >= 0 ? ` (${record.days_left} kun)` : ` (${-record.days_left} kun o'tdi)`)}
                </Tag>
              ),
            },
            { title: "Mas'ul", dataIndex: "responsible_person", render: (v: string | null) => v ?? "-" },
            { title: "Izoh", dataIndex: "notes", render: (v: string | null) => v ?? "-" },
            ...(canEdit || canDelete
              ? [
                  {
                    title: "Amallar",
                    key: "actions",
                    fixed: "right" as const,
                    width: 72,
                    render: (_: unknown, record: ServicePaymentOut) => (
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
                                      category: record.category,
                                      amount: record.amount ?? undefined,
                                      due_date: dayjs(record.due_date),
                                      responsible_person: record.responsible_person ?? undefined,
                                      notes: record.notes ?? undefined,
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
        title="Yangi to'lov"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => createForm.submit()}
        confirmLoading={saving}
        okText="Qo'shish"
        cancelText="Bekor qilish"
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="Nomi" rules={[{ required: true }]}>
            <Input placeholder="Masalan: Zoom Pro litsenziyasi" />
          </Form.Item>
          <Form.Item name="category" label="Turi" rules={[{ required: true }]}>
            <Select options={CATEGORY_OPTIONS} />
          </Form.Item>
          <Form.Item name="amount" label="Summasi">
            <InputNumber style={{ width: "100%" }} min={0} placeholder="Masalan: 150000" />
          </Form.Item>
          <Form.Item name="due_date" label="To'lov/amal qilish muddati" rules={[{ required: true }]}>
            <DatePicker style={{ width: "100%" }} format="YYYY-MM-DD" />
          </Form.Item>
          <Form.Item name="responsible_person" label="Mas'ul shaxs">
            <Input />
          </Form.Item>
          <Form.Item name="notes" label="Izoh">
            <Input.TextArea rows={2} />
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
          <Form.Item name="name" label="Nomi" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="category" label="Turi" rules={[{ required: true }]}>
            <Select options={CATEGORY_OPTIONS} />
          </Form.Item>
          <Form.Item name="amount" label="Summasi">
            <InputNumber style={{ width: "100%" }} min={0} />
          </Form.Item>
          <Form.Item name="due_date" label="To'lov/amal qilish muddati" rules={[{ required: true }]}>
            <DatePicker style={{ width: "100%" }} format="YYYY-MM-DD" />
          </Form.Item>
          <Form.Item name="responsible_person" label="Mas'ul shaxs">
            <Input />
          </Form.Item>
          <Form.Item name="notes" label="Izoh">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

import { useEffect, useState } from "react";
import { Card, Col, Row, Statistic, Spin, Table, Tag, Tooltip as AntTooltip } from "antd";
import { InfoCircleOutlined } from "@ant-design/icons";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchDashboardStats } from "../api/stats";
import type { DashboardStats } from "../types";
import { CATEGORY_LABELS_UZ } from "../types";

const STATUS_COLORS = ["#faad14", "#1677ff", "#52c41a"];

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats()
      .then(setStats)
      .finally(() => setLoading(false));
  }, []);

  if (loading || !stats) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 48 }}>
        <Spin size="large" />
      </div>
    );
  }

  const statusPieData = [
    { name: "Ochiq", value: stats.open_tickets },
    { name: "Jarayonda", value: stats.in_progress_tickets },
    { name: "Yopilgan", value: stats.closed_tickets },
  ];

  const categoryBarData = stats.category_stats.map((c) => ({
    name: CATEGORY_LABELS_UZ[c.category as keyof typeof CATEGORY_LABELS_UZ] ?? c.category,
    count: c.count,
  }));

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={3}>
          <Card>
            <Statistic title="Jami arizalar" value={stats.total_tickets} />
          </Card>
        </Col>
        <Col span={3}>
          <Card>
            <Statistic title="Ochiq" value={stats.open_tickets} valueStyle={{ color: "#faad14" }} />
          </Card>
        </Col>
        <Col span={3}>
          <Card>
            <Statistic title="Jarayonda" value={stats.in_progress_tickets} valueStyle={{ color: "#1677ff" }} />
          </Card>
        </Col>
        <Col span={3}>
          <Card>
            <Statistic title="Yopilgan" value={stats.closed_tickets} valueStyle={{ color: "#52c41a" }} />
          </Card>
        </Col>
        <Col span={3}>
          <Card>
            <Statistic title="O'rtacha baho" value={stats.average_rating ?? 0} precision={1} suffix="/ 5" />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title={
                <AntTooltip title="Muddati o'tib ketgan va hozir ham hali ochiq/jarayonda turgan arizalar soni — darhol e'tibor talab qiladi">
                  Hozir muddati o'tgan <InfoCircleOutlined style={{ fontSize: 12 }} />
                </AntTooltip>
              }
              value={stats.sla_open_breach_count}
              valueStyle={{ color: "#ff4d4f" }}
            />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic
              title={
                <AntTooltip title="Yaratilgandan buyon SLA muddati kamida bir marta buzilgan barcha arizalar (yopilganlari ham hisobga kiradi) — umumiy, kamaymaydigan hisoblagich">
                  SLA buzilishi (jami) <InfoCircleOutlined style={{ fontSize: 12 }} />
                </AntTooltip>
              }
              value={stats.sla_breach_count}
              valueStyle={{ color: "#cf7000" }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={8}>
          <Card title="Holat bo'yicha taqsimot">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={statusPieData} dataKey="value" nameKey="name" outerRadius={80}>
                  {statusPieData.map((_, index) => (
                    <Cell key={index} fill={STATUS_COLORS[index % STATUS_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend verticalAlign="bottom" height={36} />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Muammo toifalari">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={categoryBarData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={60} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#1677ff" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Vaqt bo'yicha trend (30 kun)">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={stats.daily_trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 9 }} interval={4} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#52c41a" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="Fakultetlar kesimida statistika">
            <Table
              size="small"
              rowKey="faculty_id"
              pagination={false}
              dataSource={stats.faculty_stats}
              columns={[
                { title: "Fakultet", dataIndex: "faculty_name" },
                { title: "Jami", dataIndex: "total" },
                { title: "Ochiq", dataIndex: "open" },
                { title: "Jarayonda", dataIndex: "in_progress" },
                { title: "Yopilgan", dataIndex: "closed" },
              ]}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Xodimlar ish samaradorligi">
            <Table
              size="small"
              rowKey="technician_id"
              pagination={false}
              dataSource={stats.technician_stats}
              columns={[
                { title: "FISH", dataIndex: "full_name" },
                { title: "Qabul qilingan", dataIndex: "accepted" },
                { title: "Yopilgan", dataIndex: "closed" },
                { title: "Ochiq qolgan", dataIndex: "open_remaining" },
                {
                  title: "Samaradorlik",
                  dataIndex: "efficiency_percent",
                  render: (value: number | null) => (value != null ? `${value.toFixed(0)}%` : "-"),
                },
                {
                  title: "O'rt. yopish vaqti",
                  dataIndex: "avg_close_hours",
                  render: (value: number | null) => (value != null ? `${value.toFixed(1)} soat` : "-"),
                },
              ]}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="Eng ko'p ariza yozgan foydalanuvchilar (kimda doim muammo bor)">
            <Table
              size="small"
              rowKey="user_id"
              pagination={false}
              dataSource={stats.reporter_stats}
              columns={[
                { title: "FISH", dataIndex: "full_name" },
                { title: "Telefon", dataIndex: "phone" },
                { title: "Fakultet", dataIndex: "faculty_name", render: (v: string | null) => v ?? "-" },
                {
                  title: "Jami ariza",
                  dataIndex: "total_tickets",
                  defaultSortOrder: "descend",
                  sorter: (a: { total_tickets: number }, b: { total_tickets: number }) =>
                    a.total_tickets - b.total_tickets,
                },
                { title: "Ochiq", dataIndex: "open_tickets" },
                {
                  title: "Shubhali",
                  dataIndex: "suspicious_tickets",
                  render: (v: number) => (v > 0 ? <Tag color="orange">{v}</Tag> : v),
                },
                {
                  title: "Oxirgi ariza",
                  dataIndex: "last_ticket_at",
                  render: (v: string | null) => (v ? new Date(v).toLocaleDateString("uz-UZ") : "-"),
                },
              ]}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card>
            <Statistic title="Shubhali foydalanuvchilar" value={stats.suspicious_user_count} valueStyle={{ color: "#faad14" }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Statistic title="Bloklangan foydalanuvchilar" value={stats.blocked_user_count} valueStyle={{ color: "#ff4d4f" }} />
          </Card>
        </Col>
      </Row>
    </div>
  );
}

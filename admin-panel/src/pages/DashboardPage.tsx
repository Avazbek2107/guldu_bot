import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { Card, Col, Row, Statistic, Spin, Table, Tag } from "antd";
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
  StopOutlined,
  SyncOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  LabelList,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchDashboardStats } from "../api/stats";
import { CARD_STYLE } from "../theme";
import type { DashboardStats } from "../types";
import { CATEGORY_LABELS_UZ } from "../types";

// Validated categorical slots (dataviz skill palette) — fixed order, never cycled.
const BLUE = "#2a78d6"; // chart accent (trend/category bars)
const GREEN = "#008300"; // "Yopilgan" status
const YELLOW = "#fab219"; // "Jarayonda" status
const RED = "#d03b3b"; // "Ochiq" status

const STATUS_WARNING = YELLOW;
const STATUS_CRITICAL = RED;

const INK_PRIMARY = "#0b0b0b";
const INK_SECONDARY = "#52514e";
const INK_MUTED = "#898781";
const GRIDLINE = "#e1e0d9";
const SURFACE = "#fcfcfb";

const STATUS_COLORS: Record<string, string> = {
  Ochiq: RED,
  Jarayonda: YELLOW,
  Yopilgan: GREEN,
};

const INVENTORY_STATUS_LABELS: Record<string, string> = {
  ishchi: "Ishchi",
  nosoz: "Nosoz",
  "ta'mirlanmoqda": "Ta'mirlanmoqda",
  "hisobdan chiqarilgan": "Hisobdan chiqarilgan",
};

const INVENTORY_STATUS_COLORS: Record<string, string> = {
  Ishchi: GREEN,
  Nosoz: RED,
  "Ta'mirlanmoqda": YELLOW,
  "Hisobdan chiqarilgan": INK_MUTED,
};

function KpiIcon({ icon, tint }: { icon: ReactNode; tint: string }) {
  return (
    <div
      style={{
        width: 44,
        height: 44,
        borderRadius: 12,
        background: tint,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}
    >
      {icon}
    </div>
  );
}

function CountTag({ value, color }: { value: number; color: string }) {
  return (
    <Tag color={value > 0 ? color : "default"} style={value > 0 ? undefined : { opacity: 0.35 }}>
      {value}
    </Tag>
  );
}

interface TooltipPayloadItem {
  name?: string;
  value?: number | string;
  color?: string;
  fill?: string;
  payload?: Record<string, unknown>;
}

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: SURFACE,
        border: "1px solid rgba(11,11,11,0.10)",
        borderRadius: 8,
        padding: "8px 12px",
        boxShadow: "0 4px 16px rgba(11,11,11,0.10)",
        fontSize: 13,
        minWidth: 120,
      }}
    >
      {label && <div style={{ color: INK_SECONDARY, marginBottom: 4 }}>{label}</div>}
      {payload.map((p, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: 2,
              background: p.color ?? p.fill,
              flexShrink: 0,
            }}
          />
          <span style={{ color: INK_SECONDARY }}>{p.name}:</span>
          <strong style={{ color: INK_PRIMARY }}>{p.value}</strong>
        </div>
      ))}
    </div>
  );
}

export function DashboardPage() {
  const navigate = useNavigate();
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

  const statusData = [
    { name: "Ochiq", value: stats.open_tickets },
    { name: "Jarayonda", value: stats.in_progress_tickets },
    { name: "Yopilgan", value: stats.closed_tickets },
  ];
  const totalStatusCount = statusData.reduce((sum, d) => sum + d.value, 0);
  function statusLegendFormatter(value: string) {
    const item = statusData.find((d) => d.name === value);
    const pct = item && totalStatusCount ? Math.round((item.value / totalStatusCount) * 100) : 0;
    return (
      <span style={{ color: INK_SECONDARY }}>
        {value} <strong style={{ color: INK_PRIMARY }}>{pct}%</strong>
      </span>
    );
  }

  const categoryData = stats.category_stats
    .map((c) => ({
      name: CATEGORY_LABELS_UZ[c.category as keyof typeof CATEGORY_LABELS_UZ] ?? c.category,
      count: c.count,
    }))
    .sort((a, b) => b.count - a.count);

  const inventoryStatusData = stats.inventory_status_stats.map((s) => ({
    name: INVENTORY_STATUS_LABELS[s.status] ?? s.status,
    value: s.count,
  }));
  const totalInventoryStatusCount = inventoryStatusData.reduce((sum, d) => sum + d.value, 0);
  function inventoryLegendFormatter(value: string) {
    const item = inventoryStatusData.find((d) => d.name === value);
    const pct = item && totalInventoryStatusCount ? Math.round((item.value / totalInventoryStatusCount) * 100) : 0;
    return (
      <span style={{ color: INK_SECONDARY }}>
        {value} <strong style={{ color: INK_PRIMARY }}>{pct}%</strong>
      </span>
    );
  }

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col flex="1 1 180px">
          <Card
            hoverable
            onClick={() => navigate("/tickets")}
            style={{ ...CARD_STYLE, background: BLUE, border: "none" }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <KpiIcon
                icon={<FileTextOutlined style={{ fontSize: 20, color: "#fff" }} />}
                tint="rgba(255,255,255,0.18)"
              />
              <div>
                <div style={{ fontSize: 13, color: "rgba(255,255,255,0.85)" }}>Jami arizalar</div>
                <div style={{ fontSize: 26, fontWeight: 700, color: "#fff", lineHeight: 1.2 }}>
                  {stats.total_tickets}
                </div>
              </div>
            </div>
          </Card>
        </Col>
        <Col flex="1 1 180px">
          <Card
            hoverable
            onClick={() => navigate("/tickets?status=open")}
            style={{ ...CARD_STYLE, background: RED, border: "none" }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <KpiIcon
                icon={<ExclamationCircleOutlined style={{ fontSize: 20, color: "#fff" }} />}
                tint="rgba(255,255,255,0.18)"
              />
              <div>
                <div style={{ fontSize: 13, color: "rgba(255,255,255,0.85)" }}>Ochiq</div>
                <div style={{ fontSize: 26, fontWeight: 700, color: "#fff", lineHeight: 1.2 }}>
                  {stats.open_tickets}
                </div>
              </div>
            </div>
          </Card>
        </Col>
        <Col flex="1 1 180px">
          <Card
            hoverable
            onClick={() => navigate("/tickets?status=in_progress")}
            style={{ ...CARD_STYLE, background: YELLOW, border: "none" }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <KpiIcon
                icon={<SyncOutlined style={{ fontSize: 20, color: INK_PRIMARY }} />}
                tint="rgba(11,11,11,0.10)"
              />
              <div>
                <div style={{ fontSize: 13, color: "rgba(11,11,11,0.65)" }}>Jarayonda</div>
                <div style={{ fontSize: 26, fontWeight: 700, color: INK_PRIMARY, lineHeight: 1.2 }}>
                  {stats.in_progress_tickets}
                </div>
              </div>
            </div>
          </Card>
        </Col>
        <Col flex="1 1 180px">
          <Card
            hoverable
            onClick={() => navigate("/tickets?status=closed")}
            style={{ ...CARD_STYLE, background: GREEN, border: "none" }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <KpiIcon
                icon={<CheckCircleOutlined style={{ fontSize: 20, color: "#fff" }} />}
                tint="rgba(255,255,255,0.18)"
              />
              <div>
                <div style={{ fontSize: 13, color: "rgba(255,255,255,0.85)" }}>Yopilgan</div>
                <div style={{ fontSize: 26, fontWeight: 700, color: "#fff", lineHeight: 1.2 }}>
                  {stats.closed_tickets}
                </div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={12} lg={8}>
          <Card title="Holat bo'yicha taqsimot" style={CARD_STYLE}>
            <div style={{ position: "relative" }}>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={statusData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={64}
                    outerRadius={90}
                    paddingAngle={2}
                    cornerRadius={4}
                    stroke={SURFACE}
                    strokeWidth={2}
                  >
                    {statusData.map((entry) => (
                      <Cell key={entry.name} fill={STATUS_COLORS[entry.name]} />
                    ))}
                  </Pie>
                  <Tooltip content={<ChartTooltip />} />
                  <Legend
                    verticalAlign="bottom"
                    height={36}
                    iconType="circle"
                    iconSize={8}
                    formatter={statusLegendFormatter}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div
                style={{
                  position: "absolute",
                  top: "42%",
                  left: "50%",
                  transform: "translate(-50%, -50%)",
                  textAlign: "center",
                  pointerEvents: "none",
                }}
              >
                <div style={{ fontSize: 24, fontWeight: 600, color: INK_PRIMARY, lineHeight: 1.1 }}>
                  {stats.total_tickets}
                </div>
                <div style={{ fontSize: 12, color: INK_MUTED }}>jami</div>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={12} lg={8}>
          <Card title="Muammo toifalari" style={CARD_STYLE}>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={categoryData} layout="vertical" margin={{ left: 8, right: 24 }}>
                <CartesianGrid horizontal={false} stroke={GRIDLINE} />
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: INK_MUTED }} axisLine={{ stroke: GRIDLINE }} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={110}
                  tick={{ fontSize: 11, fill: INK_SECONDARY }}
                  axisLine={{ stroke: GRIDLINE }}
                  tickLine={false}
                />
                <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(42,120,214,0.06)" }} />
                <Bar dataKey="count" fill={BLUE} radius={[0, 4, 4, 0]} maxBarSize={20} name="Arizalar">
                  <LabelList dataKey="count" position="right" style={{ fill: INK_SECONDARY, fontSize: 11 }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Vaqt bo'yicha trend (30 kun)" style={CARD_STYLE}>
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={stats.daily_trend} margin={{ left: -12, right: 12 }}>
                <defs>
                  <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={BLUE} stopOpacity={0.28} />
                    <stop offset="100%" stopColor={BLUE} stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke={GRIDLINE} />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 10, fill: INK_MUTED }}
                  tickFormatter={(value: string) => value.slice(5)}
                  interval={Math.max(0, Math.ceil(stats.daily_trend.length / 6) - 1)}
                  axisLine={{ stroke: GRIDLINE }}
                  tickLine={false}
                  minTickGap={16}
                />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: INK_MUTED }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Area
                  type="monotone"
                  dataKey="count"
                  name="Arizalar"
                  stroke={BLUE}
                  strokeWidth={2}
                  fill="url(#trendFill)"
                  dot={false}
                  activeDot={{ r: 4, stroke: SURFACE, strokeWidth: 2 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="Fakultetlar kesimida statistika" style={CARD_STYLE}>
            <Table
              size="small"
              rowKey="faculty_id"
              pagination={false}
              scroll={{ x: "max-content" }}
              dataSource={stats.faculty_stats}
              columns={[
                { title: "Fakultet", dataIndex: "faculty_name" },
                { title: "Jami", dataIndex: "total" },
                {
                  title: "Ochiq",
                  dataIndex: "open",
                  render: (v: number) => <CountTag value={v} color={RED} />,
                },
                {
                  title: "Jarayonda",
                  dataIndex: "in_progress",
                  render: (v: number) => <CountTag value={v} color={YELLOW} />,
                },
                {
                  title: "Yopilgan",
                  dataIndex: "closed",
                  render: (v: number) => <CountTag value={v} color={GREEN} />,
                },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Xodimlar ish samaradorligi" style={CARD_STYLE}>
            <Table
              size="small"
              rowKey="technician_id"
              pagination={false}
              scroll={{ x: "max-content" }}
              dataSource={stats.technician_stats}
              columns={[
                { title: "FISH", dataIndex: "full_name" },
                { title: "Qabul qilingan", dataIndex: "accepted" },
                { title: "Yopilgan", dataIndex: "closed" },
                { title: "Ochiq qolgan", dataIndex: "open_remaining" },
                {
                  title: "Samaradorlik",
                  dataIndex: "efficiency_percent",
                  sorter: (a: { efficiency_percent: number | null }, b: { efficiency_percent: number | null }) =>
                    (a.efficiency_percent ?? -1) - (b.efficiency_percent ?? -1),
                  render: (value: number | null) => {
                    if (value == null) return "-";
                    const color = value <= 50 ? RED : value <= 75 ? YELLOW : GREEN;
                    return <Tag color={color}>{value.toFixed(0)}%</Tag>;
                  },
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

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="Eng ko'p ariza yozgan foydalanuvchilar (kimda doim muammo bor)" style={CARD_STYLE}>
            <Table
              size="small"
              rowKey="user_id"
              pagination={false}
              scroll={{ x: "max-content" }}
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
                {
                  title: "Ochiq",
                  dataIndex: "open_tickets",
                  render: (v: number) => <CountTag value={v} color={RED} />,
                },
                {
                  title: "Shubhali",
                  dataIndex: "suspicious_tickets",
                  render: (v: number) => <CountTag value={v} color="orange" />,
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

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={8}>
          <Card title="Inventar holati bo'yicha taqsimot" style={CARD_STYLE}>
            <div style={{ position: "relative" }}>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={inventoryStatusData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={64}
                    outerRadius={90}
                    paddingAngle={2}
                    cornerRadius={4}
                    stroke={SURFACE}
                    strokeWidth={2}
                  >
                    {inventoryStatusData.map((entry) => (
                      <Cell key={entry.name} fill={INVENTORY_STATUS_COLORS[entry.name] ?? INK_MUTED} />
                    ))}
                  </Pie>
                  <Tooltip content={<ChartTooltip />} />
                  <Legend
                    verticalAlign="bottom"
                    height={48}
                    iconType="circle"
                    iconSize={8}
                    formatter={inventoryLegendFormatter}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div
                style={{
                  position: "absolute",
                  top: "42%",
                  left: "50%",
                  transform: "translate(-50%, -50%)",
                  textAlign: "center",
                  pointerEvents: "none",
                }}
              >
                <div style={{ fontSize: 24, fontWeight: 600, color: INK_PRIMARY, lineHeight: 1.1 }}>
                  {stats.total_inventory_items}
                </div>
                <div style={{ fontSize: 12, color: INK_MUTED }}>jami</div>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={16}>
          <Card title="Inventar hisoboti — yo'nalishlar kesimida" style={CARD_STYLE}>
            <Table
              size="small"
              rowKey="faculty_id"
              pagination={false}
              scroll={{ x: "max-content", y: 260 }}
              dataSource={stats.inventory_faculty_stats}
              columns={[
                { title: "Yo'nalish", dataIndex: "faculty_name" },
                { title: "Jami", dataIndex: "total", defaultSortOrder: "descend", sorter: (a: { total: number }, b: { total: number }) => a.total - b.total },
                {
                  title: "Ishchi",
                  dataIndex: "working",
                  render: (v: number) => <CountTag value={v} color={GREEN} />,
                },
                {
                  title: "Nosoz",
                  dataIndex: "broken",
                  render: (v: number) => <CountTag value={v} color={RED} />,
                },
                {
                  title: "Ta'mirlanmoqda",
                  dataIndex: "in_repair",
                  render: (v: number) => <CountTag value={v} color={YELLOW} />,
                },
                {
                  title: "Hisobdan chiqarilgan",
                  dataIndex: "decommissioned",
                  render: (v: number) => <CountTag value={v} color={INK_MUTED} />,
                },
              ]}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} sm={12}>
          <Card style={CARD_STYLE}>
            <Statistic
              title={
                <span>
                  <WarningOutlined style={{ color: STATUS_WARNING, marginRight: 6 }} />
                  Shubhali foydalanuvchilar
                </span>
              }
              value={stats.suspicious_user_count}
              valueStyle={{ color: STATUS_WARNING }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12}>
          <Card style={CARD_STYLE}>
            <Statistic
              title={
                <span>
                  <StopOutlined style={{ color: STATUS_CRITICAL, marginRight: 6 }} />
                  Bloklangan foydalanuvchilar
                </span>
              }
              value={stats.blocked_user_count}
              valueStyle={{ color: STATUS_CRITICAL }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}

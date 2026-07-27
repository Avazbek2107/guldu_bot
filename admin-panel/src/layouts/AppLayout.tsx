import { useState } from "react";
import { Layout, Menu, Button, Avatar, Dropdown, Tag, Drawer, Grid, Space } from "antd";
import type { MenuProps } from "antd";
import {
  DashboardOutlined,
  UnorderedListOutlined,
  TeamOutlined,
  UserOutlined,
  BankOutlined,
  ClusterOutlined,
  DatabaseOutlined,
  LogoutOutlined,
  MenuOutlined,
  DownOutlined,
} from "@ant-design/icons";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ROLE_LABELS_UZ, type UserRole } from "../types";

const { Header, Sider, Content } = Layout;
const { useBreakpoint } = Grid;

const ROLE_COLORS: Record<UserRole, string> = {
  super_admin: "gold",
  technician_main: "blue",
  technician_backup: "cyan",
  faculty_staff: "green",
};

const ROLE_AVATAR_COLORS: Record<UserRole, string> = {
  super_admin: "#faad14",
  technician_main: "#1677ff",
  technician_backup: "#13c2c2",
  faculty_staff: "#52c41a",
};

function initials(fullName: string): string {
  return fullName
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const screens = useBreakpoint();
  const isMobile = !screens.lg;
  const [drawerOpen, setDrawerOpen] = useState(false);

  const isSuperAdmin = user?.role === "super_admin";

  const menuItems = [
    isSuperAdmin ? { key: "/dashboard", icon: <DashboardOutlined />, label: "Dashboard" } : null,
    { key: "/tickets", icon: <UnorderedListOutlined />, label: "Arizalar" },
    { key: "/inventory", icon: <DatabaseOutlined />, label: "Inventar" },
    isSuperAdmin ? { key: "/users", icon: <TeamOutlined />, label: "Xodimlar" } : null,
    isSuperAdmin ? { key: "/end-users", icon: <UserOutlined />, label: "Foydalanuvchilar" } : null,
    isSuperAdmin ? { key: "/faculties", icon: <BankOutlined />, label: "Fakultetlar" } : null,
    isSuperAdmin ? { key: "/departments", icon: <ClusterOutlined />, label: "Bo'limlar" } : null,
  ].filter((item): item is NonNullable<typeof item> => item !== null);

  const menu = (
    <Menu
      theme="dark"
      mode="inline"
      selectedKeys={[location.pathname]}
      items={menuItems}
      onClick={({ key }) => {
        navigate(key);
        setDrawerOpen(false);
      }}
    />
  );

  const brand = (
    <div style={{ color: "white", textAlign: "center", padding: 16, fontWeight: 600 }}>Texnik Yordam</div>
  );

  const userMenuItems: MenuProps["items"] = [
    {
      key: "info",
      label: (
        <div style={{ padding: "2px 4px", cursor: "default" }}>
          <div style={{ fontWeight: 600 }}>{user?.full_name}</div>
          {user && (
            <Tag color={ROLE_COLORS[user.role]} style={{ marginTop: 4 }}>
              {ROLE_LABELS_UZ[user.role]}
            </Tag>
          )}
        </div>
      ),
      disabled: true,
    },
    { type: "divider" },
    { key: "logout", icon: <LogoutOutlined />, label: "Chiqish", danger: true },
  ];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      {!isMobile && (
        <Sider>
          {brand}
          {menu}
        </Sider>
      )}
      {isMobile && (
        <Drawer
          placement="left"
          closable={false}
          onClose={() => setDrawerOpen(false)}
          open={drawerOpen}
          width={220}
          styles={{ body: { padding: 0, background: "#001529" } }}
        >
          {brand}
          {menu}
        </Drawer>
      )}
      <Layout>
        <Header
          style={{
            background: "#fff",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: isMobile ? "0 12px" : "0 24px",
            gap: 8,
          }}
        >
          <Space size="small" style={{ minWidth: 0 }}>
            {isMobile && <Button icon={<MenuOutlined />} onClick={() => setDrawerOpen(true)} />}
          </Space>
          <Dropdown
            menu={{ items: userMenuItems, onClick: ({ key }) => key === "logout" && logout() }}
            trigger={["click"]}
            placement="bottomRight"
          >
            <Space size={8} style={{ cursor: "pointer", minWidth: 0 }}>
              <Avatar style={{ backgroundColor: user ? ROLE_AVATAR_COLORS[user.role] : "#1677ff", flexShrink: 0 }}>
                {user ? initials(user.full_name) : ""}
              </Avatar>
              {!isMobile && (
                <span style={{ maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {user?.full_name}
                </span>
              )}
              <DownOutlined style={{ fontSize: 10, color: "rgba(0,0,0,0.45)" }} />
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: isMobile ? 12 : 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}

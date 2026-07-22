import { Layout, Menu, Button, Typography } from "antd";
import {
  DashboardOutlined,
  UnorderedListOutlined,
  TeamOutlined,
  BankOutlined,
  LogoutOutlined,
} from "@ant-design/icons";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ROLE_LABELS_UZ } from "../types";

const { Header, Sider, Content } = Layout;

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const isSuperAdmin = user?.role === "super_admin";

  const menuItems = [
    isSuperAdmin ? { key: "/dashboard", icon: <DashboardOutlined />, label: "Dashboard" } : null,
    { key: "/tickets", icon: <UnorderedListOutlined />, label: "Arizalar" },
    isSuperAdmin ? { key: "/users", icon: <TeamOutlined />, label: "Foydalanuvchilar" } : null,
    isSuperAdmin ? { key: "/faculties", icon: <BankOutlined />, label: "Fakultetlar" } : null,
  ].filter((item): item is NonNullable<typeof item> => item !== null);

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider>
        <div style={{ color: "white", textAlign: "center", padding: 16, fontWeight: 600 }}>Texnik Yordam</div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: "#fff",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "0 24px",
          }}
        >
          <Typography.Text>
            {user?.full_name} — {user ? ROLE_LABELS_UZ[user.role] : ""}
          </Typography.Text>
          <Button icon={<LogoutOutlined />} onClick={logout}>
            Chiqish
          </Button>
        </Header>
        <Content style={{ margin: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}

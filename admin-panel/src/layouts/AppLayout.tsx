import { useState } from "react";
import { isAxiosError } from "axios";
import { Layout, Menu, Button, Avatar, Dropdown, Tag, Drawer, Grid, Space, Modal, Form, Input, Divider, message } from "antd";
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
  EditOutlined,
} from "@ant-design/icons";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { updateProfile } from "../api/auth";
import { csrfState } from "../api/client";
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

interface ProfileFormValues {
  full_name: string;
  username: string;
  current_password?: string;
  new_password?: string;
}

export function AppLayout() {
  const { user, logout, setUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const screens = useBreakpoint();
  const isMobile = !screens.lg;
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileForm] = Form.useForm<ProfileFormValues>();

  const isSuperAdmin = user?.role === "super_admin";

  function openProfileModal() {
    if (!user) return;
    profileForm.setFieldsValue({
      full_name: user.full_name,
      username: user.username ?? "",
      current_password: undefined,
      new_password: undefined,
    });
    setProfileOpen(true);
  }

  async function handleProfileSave(values: ProfileFormValues) {
    setProfileSaving(true);
    try {
      const payload: Parameters<typeof updateProfile>[0] = {
        full_name: values.full_name,
        username: values.username,
      };
      if (values.new_password) {
        payload.new_password = values.new_password;
      }
      if (values.username !== user?.username || values.new_password) {
        payload.current_password = values.current_password;
      }
      const response = await updateProfile(payload);
      csrfState.token = response.csrf_token;
      setUser(response.user);
      message.success("Profil yangilandi");
      setProfileOpen(false);
      profileForm.resetFields();
    } catch (error) {
      const detail =
        isAxiosError<{ detail?: string }>(error) && error.response?.data?.detail
          ? error.response.data.detail
          : "Xatolik yuz berdi";
      message.error(detail);
    } finally {
      setProfileSaving(false);
    }
  }

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
    { key: "profile", icon: <EditOutlined />, label: "Profilni tahrirlash" },
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
            menu={{
              items: userMenuItems,
              onClick: ({ key }) => {
                if (key === "logout") logout();
                if (key === "profile") openProfileModal();
              },
            }}
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

      <Modal
        title="Profilni tahrirlash"
        open={profileOpen}
        onCancel={() => setProfileOpen(false)}
        onOk={() => profileForm.submit()}
        confirmLoading={profileSaving}
        okText="Saqlash"
        cancelText="Bekor qilish"
      >
        <Form form={profileForm} layout="vertical" onFinish={handleProfileSave}>
          <Form.Item name="full_name" label="FISH" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="username" label="Login" rules={[{ required: true, min: 3 }]}>
            <Input />
          </Form.Item>
          <Divider style={{ margin: "12px 0" }}>Parolni o'zgartirish (ixtiyoriy)</Divider>
          <Form.Item name="new_password" label="Yangi parol" rules={[{ min: 8, message: "Kamida 8 ta belgi" }]}>
            <Input.Password placeholder="Bo'sh qoldirsangiz, parol o'zgarmaydi" />
          </Form.Item>
          <Form.Item
            name="current_password"
            label="Joriy parol"
            extra="Login yoki parolni o'zgartirish uchun joriy parolingizni kiriting"
          >
            <Input.Password />
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  );
}

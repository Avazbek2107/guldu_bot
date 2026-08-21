import { useRef, useState, type ChangeEvent } from "react";
import { isAxiosError } from "axios";
import {
  Layout,
  Menu,
  Button,
  Avatar,
  Dropdown,
  Drawer,
  Grid,
  Space,
  Modal,
  Form,
  Input,
  Divider,
  message,
} from "antd";
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
  CameraOutlined,
  CrownOutlined,
  ProjectOutlined,
  WalletOutlined,
} from "@ant-design/icons";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { updateProfile, uploadAvatar } from "../api/auth";
import { csrfState, resolveAssetUrl } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { hasPermission } from "../auth/permissions";
import { ROLE_LABELS_UZ, type UserRole } from "../types";

const { Header, Sider, Content } = Layout;
const { useBreakpoint } = Grid;

const ROLE_COLORS: Record<UserRole, [string, string]> = {
  super_admin: ["#7c3aed", "#5b21b6"],
  admin: ["#db2777", "#9d174d"],
  technician_main: ["#2563eb", "#1e40af"],
  technician_backup: ["#0891b2", "#155e75"],
  faculty_staff: ["#16a34a", "#166534"],
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
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [profileForm] = Form.useForm<ProfileFormValues>();
  const avatarInputRef = useRef<HTMLInputElement | null>(null);

  const [roleColor, roleColorDark] = user ? ROLE_COLORS[user.role] : ["#2563eb", "#1e40af"];
  const avatarSrc = user?.avatar_url ? resolveAssetUrl(user.avatar_url) : undefined;

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

  async function handleAvatarFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setAvatarUploading(true);
    try {
      const response = await uploadAvatar(file);
      csrfState.token = response.csrf_token;
      setUser(response.user);
      message.success("Rasm yangilandi");
    } catch (error) {
      const detail =
        isAxiosError<{ detail?: string }>(error) && error.response?.data?.detail
          ? error.response.data.detail
          : "Rasmni yuklashda xatolik yuz berdi";
      message.error(detail);
    } finally {
      setAvatarUploading(false);
    }
  }

  const isTechnician = user?.role === "technician_main" || user?.role === "technician_backup";
  const canSeeTickets = isTechnician || hasPermission(user, "tickets");
  const canSeeInventory = isTechnician || hasPermission(user, "inventory");

  const menuItems = [
    hasPermission(user, "dashboard") ? { key: "/dashboard", icon: <DashboardOutlined />, label: "Dashboard" } : null,
    hasPermission(user, "users") ? { key: "/users", icon: <TeamOutlined />, label: "Xodimlar" } : null,
    canSeeTickets ? { key: "/tickets", icon: <UnorderedListOutlined />, label: "Arizalar" } : null,
    canSeeInventory ? { key: "/inventory", icon: <DatabaseOutlined />, label: "Inventar" } : null,
    hasPermission(user, "end_users")
      ? { key: "/end-users", icon: <UserOutlined />, label: "Foydalanuvchilar" }
      : null,
    hasPermission(user, "faculties") ? { key: "/faculties", icon: <BankOutlined />, label: "Fakultetlar" } : null,
    hasPermission(user, "departments")
      ? { key: "/departments", icon: <ClusterOutlined />, label: "Bo'limlar" }
      : null,
    hasPermission(user, "projects")
      ? { key: "/projects", icon: <ProjectOutlined />, label: "Markaz loyihalar" }
      : null,
    hasPermission(user, "payments")
      ? { key: "/payments", icon: <WalletOutlined />, label: "To'lovlar monitoringi" }
      : null,
    hasPermission(user, "users") ? { key: "/admins", icon: <CrownOutlined />, label: "Boshqaruv" } : null,
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

  const userMenuItems = [
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
            popupRender={(menuNode) => (
              <div style={{ borderRadius: 8, overflow: "hidden", boxShadow: "0 6px 16px rgba(11,11,11,0.16)" }}>
                <div
                  style={{
                    background: `linear-gradient(135deg, ${roleColor}, ${roleColorDark})`,
                    padding: "14px 16px",
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                  }}
                >
                  <Avatar
                    size={40}
                    src={avatarSrc}
                    style={{ backgroundColor: "rgba(255,255,255,0.25)", flexShrink: 0 }}
                  >
                    {!avatarSrc && user ? initials(user.full_name) : null}
                  </Avatar>
                  <div style={{ minWidth: 0 }}>
                    <div
                      style={{
                        color: "#fff",
                        fontWeight: 600,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {user?.full_name}
                    </div>
                    <div style={{ color: "rgba(255,255,255,0.85)", fontSize: 12 }}>
                      {user ? ROLE_LABELS_UZ[user.role] : ""}
                    </div>
                  </div>
                </div>
                {menuNode}
              </div>
            )}
          >
            <Space size={8} style={{ cursor: "pointer", minWidth: 0 }}>
              <Avatar src={avatarSrc} style={{ backgroundColor: roleColor, flexShrink: 0 }}>
                {!avatarSrc && user ? initials(user.full_name) : ""}
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
        <div style={{ display: "flex", justifyContent: "center", marginBottom: 20 }}>
          <div style={{ position: "relative" }}>
            <Avatar size={72} src={avatarSrc} style={{ backgroundColor: roleColor }}>
              {!avatarSrc && user ? initials(user.full_name) : null}
            </Avatar>
            <Button
              shape="circle"
              size="small"
              icon={<CameraOutlined />}
              loading={avatarUploading}
              style={{ position: "absolute", bottom: -2, right: -2 }}
              onClick={() => avatarInputRef.current?.click()}
            />
            <input
              ref={avatarInputRef}
              type="file"
              accept="image/png,image/jpeg,image/webp"
              style={{ display: "none" }}
              onChange={handleAvatarFile}
            />
          </div>
        </div>
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

import { useState } from "react";
import { Button, Card, Form, Input, Typography, message } from "antd";
import { LockOutlined, UserOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

interface LoginFormValues {
  username: string;
  password: string;
}

function Logo() {
  const [failed, setFailed] = useState(false);

  if (failed) {
    return (
      <div
        style={{
          width: 72,
          height: 72,
          margin: "0 auto",
          borderRadius: "50%",
          background: "linear-gradient(135deg, #7e14ff, #47bfff)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#fff",
          fontWeight: 700,
          fontSize: 20,
          letterSpacing: 0.5,
        }}
      >
        GulDU
      </div>
    );
  }

  return (
    <img
      src="/logo.png"
      alt="Guliston davlat universiteti"
      onError={() => setFailed(true)}
      style={{ width: 72, height: 72, margin: "0 auto", display: "block", objectFit: "contain" }}
    />
  );
}

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  async function handleFinish(values: LoginFormValues) {
    setLoading(true);
    try {
      await login(values.username, values.password);
      navigate("/", { replace: true });
    } catch {
      message.error("Login yoki parol noto'g'ri");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        padding: 16,
        background: "#f0f2f5",
      }}
    >
      <Card
        style={{
          width: 380,
          maxWidth: "100%",
          borderRadius: 20,
          boxShadow: "0 20px 45px -12px rgba(76, 29, 149, 0.25)",
          border: "none",
        }}
        styles={{ body: { padding: "36px 32px" } }}
      >
        <Logo />
        <Typography.Title level={3} style={{ textAlign: "center", marginTop: 20, marginBottom: 2 }}>
          Texnik Yordam Tizimi
        </Typography.Title>
        <Typography.Text
          type="secondary"
          style={{ display: "block", textAlign: "center", marginBottom: 28 }}
        >
          Guliston davlat universiteti
        </Typography.Text>
        <Form layout="vertical" onFinish={handleFinish} requiredMark={false}>
          <Form.Item name="username" label="Login" rules={[{ required: true, message: "Login kiriting" }]}>
            <Input size="large" prefix={<UserOutlined style={{ color: "rgba(0,0,0,0.35)" }} />} autoFocus />
          </Form.Item>
          <Form.Item name="password" label="Parol" rules={[{ required: true, message: "Parol kiriting" }]}>
            <Input.Password size="large" prefix={<LockOutlined style={{ color: "rgba(0,0,0,0.35)" }} />} />
          </Form.Item>
          <Form.Item style={{ marginTop: 24, marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" block size="large" loading={loading} style={{ borderRadius: 10 }}>
              Kirish
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}

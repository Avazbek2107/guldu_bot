import { useState } from "react";
import { Button, Card, Form, Input, Typography, message } from "antd";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

interface LoginFormValues {
  username: string;
  password: string;
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
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh", background: "#f0f2f5" }}>
      <Card style={{ width: 360 }}>
        <Typography.Title level={3} style={{ textAlign: "center" }}>
          Texnik Yordam Tizimi
        </Typography.Title>
        <Form layout="vertical" onFinish={handleFinish}>
          <Form.Item name="username" label="Login" rules={[{ required: true, message: "Login kiriting" }]}>
            <Input autoFocus />
          </Form.Item>
          <Form.Item name="password" label="Parol" rules={[{ required: true, message: "Parol kiriting" }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              Kirish
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}

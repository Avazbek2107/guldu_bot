import type { ReactNode } from "react";
import { Button, Dropdown, Modal } from "antd";
import { MoreOutlined } from "@ant-design/icons";
import type { MenuProps } from "antd";

export interface ActionItem {
  key: string;
  label: string;
  icon?: ReactNode;
  danger?: boolean;
  disabled?: boolean;
  /** If set, a confirmation dialog is shown before onClick runs. */
  confirmTitle?: string;
  onClick: () => void;
}

export function ActionsMenu({ items }: { items: ActionItem[] }) {
  const menuItems: MenuProps["items"] = items.map((item) => ({
    key: item.key,
    label: item.label,
    icon: item.icon,
    danger: item.danger,
    disabled: item.disabled,
  }));

  function handleMenuClick({ key }: { key: string }) {
    const item = items.find((i) => i.key === key);
    if (!item) return;
    if (item.confirmTitle) {
      Modal.confirm({
        title: item.confirmTitle,
        okText: "Ha",
        okType: item.danger ? "danger" : "primary",
        cancelText: "Bekor qilish",
        onOk: item.onClick,
      });
    } else {
      item.onClick();
    }
  }

  return (
    <Dropdown menu={{ items: menuItems, onClick: handleMenuClick }} trigger={["click"]} placement="bottomRight">
      <Button size="small" icon={<MoreOutlined />} />
    </Dropdown>
  );
}

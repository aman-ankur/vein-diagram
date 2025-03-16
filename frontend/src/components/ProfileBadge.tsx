import React from 'react';
import { Badge, Avatar, Dropdown, Menu, Button, Spin } from 'antd';
import { UserOutlined, DownOutlined, LogoutOutlined, EditOutlined } from '@ant-design/icons';
import { useProfile } from '../contexts/ProfileContext';
import { useNavigate } from 'react-router-dom';

const ProfileBadge: React.FC = () => {
  const { activeProfile, setActiveProfileById, loading } = useProfile();
  const navigate = useNavigate();

  const handleProfileManagement = () => {
    navigate('/profiles');
  };

  const handleLogout = () => {
    setActiveProfileById(null);
  };

  const menu = (
    <Menu>
      <Menu.Item key="profile" icon={<EditOutlined />} onClick={handleProfileManagement}>
        Manage Profiles
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item key="logout" icon={<LogoutOutlined />} onClick={handleLogout}>
        Switch Profile
      </Menu.Item>
    </Menu>
  );

  if (loading) {
    return <Spin size="small" />;
  }

  if (!activeProfile) {
    return (
      <Button type="primary" onClick={handleProfileManagement}>
        Select Profile
      </Button>
    );
  }

  return (
    <Dropdown overlay={menu} trigger={['click']}>
      <div className="profile-badge" style={{ cursor: 'pointer' }}>
        <Badge status="success" dot>
          <Avatar icon={<UserOutlined />} />
        </Badge>
        <span className="profile-name" style={{ marginLeft: 8, marginRight: 4 }}>
          {activeProfile.name}
        </span>
        <DownOutlined style={{ fontSize: '12px' }} />
      </div>
    </Dropdown>
  );
};

export default ProfileBadge; 
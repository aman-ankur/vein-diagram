import React, { useState, useEffect } from 'react';
import { Profile } from '../types/Profile';
import { getProfiles } from '../services/profileService';
import { Button, Select, Input, Spin, Modal, Form, DatePicker } from 'antd';
import { PlusOutlined, UserOutlined } from '@ant-design/icons';
import moment from 'moment';

interface ProfileSelectorProps {
  selectedProfileId: string | null;
  onProfileSelect: (profileId: string | null) => void;
  onCreateProfile: (name: string, dateOfBirth?: string, gender?: string, patientId?: string) => Promise<void>;
}

const ProfileSelector: React.FC<ProfileSelectorProps> = ({
  selectedProfileId,
  onProfileSelect,
  onCreateProfile,
}) => {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [isModalVisible, setIsModalVisible] = useState<boolean>(false);
  const [form] = Form.useForm();

  // Fetch profiles on component mount and when search term changes
  useEffect(() => {
    const fetchProfiles = async () => {
      try {
        setLoading(true);
        const response = await getProfiles(searchTerm);
        setProfiles(response.profiles);
        setError(null);
      } catch (err) {
        setError('Failed to load profiles. Please try again.');
        console.error('Error fetching profiles:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchProfiles();
  }, [searchTerm]);

  const handleProfileChange = (value: string) => {
    onProfileSelect(value);
  };

  const handleSearch = (value: string) => {
    setSearchTerm(value);
  };

  const showCreateModal = () => {
    setIsModalVisible(true);
  };

  const handleCancel = () => {
    setIsModalVisible(false);
    form.resetFields();
  };

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      
      // Format date if provided
      const dateOfBirth = values.dateOfBirth 
        ? moment(values.dateOfBirth).format('YYYY-MM-DD') 
        : undefined;
      
      await onCreateProfile(
        values.name,
        dateOfBirth,
        values.gender,
        values.patientId
      );
      
      setIsModalVisible(false);
      form.resetFields();
      
      // Refresh profiles list
      const response = await getProfiles(searchTerm);
      setProfiles(response.profiles);
    } catch (err) {
      console.error('Failed to create profile:', err);
    }
  };

  return (
    <div className="profile-selector">
      <div className="profile-selector-header">
        <h3>Select Profile</h3>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={showCreateModal}
        >
          New Profile
        </Button>
      </div>
      
      {loading ? (
        <Spin tip="Loading profiles..." />
      ) : error ? (
        <div className="error-message">{error}</div>
      ) : (
        <div className="profile-select-container">
          <Select
            showSearch
            style={{ width: '100%' }}
            placeholder="Select a profile"
            optionFilterProp="children"
            onChange={handleProfileChange}
            onSearch={handleSearch}
            value={selectedProfileId || undefined}
            filterOption={(input, option) =>
              (option?.label as string).toLowerCase().includes(input.toLowerCase())
            }
            options={profiles.map((profile) => ({
              value: profile.id,
              label: `${profile.name}${profile.patient_id ? ` (ID: ${profile.patient_id})` : ''}`,
            }))}
          />
        </div>
      )}

      <Modal
        title="Create New Profile"
        open={isModalVisible}
        onOk={handleCreate}
        onCancel={handleCancel}
      >
        <Form
          form={form}
          layout="vertical"
          name="profile_form"
        >
          <Form.Item
            name="name"
            label="Name"
            rules={[{ required: true, message: 'Please enter a name' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="Full Name" />
          </Form.Item>
          
          <Form.Item
            name="dateOfBirth"
            label="Date of Birth"
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item
            name="gender"
            label="Gender"
          >
            <Select placeholder="Select gender">
              <Select.Option value="male">Male</Select.Option>
              <Select.Option value="female">Female</Select.Option>
              <Select.Option value="other">Other</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="patientId"
            label="Patient ID"
          >
            <Input placeholder="Patient ID from lab reports" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ProfileSelector; 
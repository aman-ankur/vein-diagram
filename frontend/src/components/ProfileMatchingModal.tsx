import React, { useState, useEffect } from 'react';
import { Modal, Button, Card, Avatar, Divider, Space, Row, Col, Progress, Form, Input, DatePicker, Select, Typography } from 'antd';
import { UserOutlined, CheckCircleOutlined, PlusCircleOutlined } from '@ant-design/icons';
import { Profile, ProfileMatch, ProfileMetadata } from '../types/Profile';
import moment from 'moment';

const { Title, Text } = Typography;
const { Option } = Select;

interface ProfileMatchingModalProps {
  visible: boolean;
  pdfId: string;
  matches: ProfileMatch[];
  metadata: ProfileMetadata;
  onCancel: () => void;
  onSelectProfile: (profileId: string) => void;
  onCreateNewProfile: (metadata: ProfileMetadata) => void;
  loading: boolean;
}

const ProfileMatchingModal: React.FC<ProfileMatchingModalProps> = ({
  visible,
  pdfId,
  matches,
  metadata,
  onCancel,
  onSelectProfile,
  onCreateNewProfile,
  loading
}) => {
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
  const [createNew, setCreateNew] = useState<boolean>(false);
  const [form] = Form.useForm();
  
  // When matches change or modal becomes visible, pre-select highest confidence match
  useEffect(() => {
    if (visible && matches.length > 0) {
      // Sort by confidence and select the highest
      const sortedMatches = [...matches].sort((a, b) => b.confidence - a.confidence);
      setSelectedProfileId(sortedMatches[0].profile.id);
      setCreateNew(false);
    } else {
      setSelectedProfileId(null);
      setCreateNew(matches.length === 0);
    }
  }, [visible, matches]);
  
  // When metadata changes, update form values
  useEffect(() => {
    if (visible && createNew) {
      form.setFieldsValue({
        name: metadata.patient_name || '',
        gender: metadata.patient_gender?.toLowerCase() || '',
        patient_id: metadata.patient_id || '',
        date_of_birth: metadata.patient_dob ? moment(metadata.patient_dob) : undefined
      });
    }
  }, [visible, createNew, metadata, form]);
  
  const handleSelect = (profileId: string) => {
    setSelectedProfileId(profileId);
    setCreateNew(false);
  };
  
  const handleCreateNew = () => {
    setSelectedProfileId(null);
    setCreateNew(true);
    
    // Pre-fill form with metadata
    form.setFieldsValue({
      name: metadata.patient_name || '',
      gender: metadata.patient_gender?.toLowerCase() || '',
      patient_id: metadata.patient_id || '',
      date_of_birth: metadata.patient_dob ? moment(metadata.patient_dob) : undefined
    });
  };
  
  const handleConfirm = () => {
    if (createNew) {
      // Submit form for validation
      form.validateFields().then(values => {
        const newMetadata: ProfileMetadata = {
          ...metadata,
          patient_name: values.name,
          patient_gender: values.gender,
          patient_id: values.patient_id,
          patient_dob: values.date_of_birth ? values.date_of_birth.format('YYYY-MM-DD') : undefined
        };
        
        onCreateNewProfile(newMetadata);
      }).catch(info => {
        console.log('Validate Failed:', info);
      });
    } else if (selectedProfileId) {
      onSelectProfile(selectedProfileId);
    }
  };
  
  const renderProfileCard = (match: ProfileMatch) => {
    const { profile, confidence } = match;
    const isSelected = selectedProfileId === profile.id;
    
    return (
      <Card 
        key={profile.id}
        className={`profile-match-card ${isSelected ? 'selected' : ''}`}
        style={{ 
          marginBottom: 16, 
          cursor: 'pointer',
          border: isSelected ? '2px solid #1890ff' : '1px solid #d9d9d9',
          backgroundColor: isSelected ? '#f0f8ff' : 'white'
        }}
        onClick={() => handleSelect(profile.id)}
      >
        <Row align="middle" gutter={16}>
          <Col span={4}>
            <Avatar size={64} icon={<UserOutlined />} style={{ backgroundColor: isSelected ? '#1890ff' : '#ccc' }} />
          </Col>
          <Col span={16}>
            <Title level={5}>{profile.name}</Title>
            <Space direction="vertical" size={0}>
              {profile.date_of_birth && (
                <Text type="secondary">Born: {moment(profile.date_of_birth).format('MMM D, YYYY')}</Text>
              )}
              {profile.gender && (
                <Text type="secondary">Gender: {profile.gender}</Text>
              )}
              {profile.patient_id && (
                <Text type="secondary">Patient ID: {profile.patient_id}</Text>
              )}
              <Text type="secondary">
                {profile.biomarker_count} biomarkers from {profile.pdf_count} reports
              </Text>
            </Space>
          </Col>
          <Col span={4}>
            <Progress
              type="circle"
              percent={Math.round(confidence * 100)}
              width={50}
              format={percent => `${percent}%`}
              status={confidence > 0.8 ? 'success' : undefined}
            />
          </Col>
        </Row>
      </Card>
    );
  };
  
  return (
    <Modal
      title="Link Lab Report to Profile"
      open={visible}
      width={800}
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          Cancel
        </Button>,
        <Button 
          key="confirm" 
          type="primary" 
          onClick={handleConfirm}
          disabled={!selectedProfileId && !createNew}
          loading={loading}
        >
          Confirm Selection
        </Button>
      ]}
    >
      {matches.length > 0 && (
        <div className="profile-matches">
          <Title level={4}>
            <CheckCircleOutlined /> Matching Profiles
          </Title>
          <Text type="secondary">
            We found these existing profiles that might match this lab report. 
            Select one to link this report to that profile.
          </Text>
          <Divider />
          {matches.map(match => renderProfileCard(match))}
        </div>
      )}
      
      <div className="create-new-profile">
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
          <Title level={4} style={{ margin: 0, marginRight: 16 }}>
            <PlusCircleOutlined /> Create New Profile
          </Title>
          <Button 
            type={createNew ? 'primary' : 'default'} 
            onClick={handleCreateNew}
          >
            {createNew ? 'Selected' : 'Select'}
          </Button>
        </div>
        
        {createNew && (
          <Form
            form={form}
            layout="vertical"
            initialValues={{
              name: metadata.patient_name || '',
              gender: metadata.patient_gender?.toLowerCase() || '',
              patient_id: metadata.patient_id || '',
              date_of_birth: metadata.patient_dob ? moment(metadata.patient_dob) : undefined
            }}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="name"
                  label="Name"
                  rules={[{ required: true, message: 'Please enter a name' }]}
                >
                  <Input placeholder="Full Name" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="date_of_birth"
                  label="Date of Birth"
                >
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="gender"
                  label="Gender"
                >
                  <Select placeholder="Select gender">
                    <Option value="male">Male</Option>
                    <Option value="female">Female</Option>
                    <Option value="other">Other</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="patient_id"
                  label="Patient ID"
                >
                  <Input placeholder="Patient ID from lab reports" />
                </Form.Item>
              </Col>
            </Row>
          </Form>
        )}
      </div>
    </Modal>
  );
};

export default ProfileMatchingModal; 
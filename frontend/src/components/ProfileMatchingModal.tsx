import React, { useState, useEffect } from 'react';
import { Modal, Button, Card, Avatar, Divider, Space, Row, Col, Progress, Form, Input, DatePicker, Select, Typography, Alert } from 'antd';
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
    if (visible) {
      console.log("ProfileMatchingModal became visible with metadata:", metadata);
      console.log("Available matches:", matches);
      
      if (matches && matches.length > 0) {
        // Sort by confidence and select the highest
        const sortedMatches = [...matches].sort((a, b) => b.confidence - a.confidence);
        setSelectedProfileId(sortedMatches[0].profile.id);
        setCreateNew(false);
        console.log("Selected highest confidence match:", sortedMatches[0].profile.name, `(${Math.round(sortedMatches[0].confidence * 100)}%)`);
      } else {
        setSelectedProfileId(null);
        setCreateNew(true);
        console.log("No matches found, defaulting to create new profile");
      }
    }
  }, [visible, matches]);
  
  // When metadata changes, update form values
  useEffect(() => {
    if (visible && createNew) {
      console.log("Updating form with metadata:", metadata);
      
      // Format the date if it exists
      let dateObj = undefined;
      if (metadata.patient_dob) {
        try {
          dateObj = moment(metadata.patient_dob);
          console.log("Parsed DOB:", dateObj.format('YYYY-MM-DD'));
        } catch (e) {
          console.error("Error parsing date:", e);
        }
      }
      
      form.setFieldsValue({
        name: metadata.patient_name || '',
        gender: metadata.patient_gender?.toLowerCase() || '',
        patient_id: metadata.patient_id || '',
        date_of_birth: dateObj
      });
    }
  }, [visible, createNew, metadata, form]);
  
  const handleSelect = (profileId: string) => {
    console.log("Selected profile:", profileId);
    setSelectedProfileId(profileId);
    setCreateNew(false);
  };
  
  const handleCreateNew = () => {
    console.log("User chose to create a new profile");
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
      console.log("Confirming new profile creation");
      // Submit form for validation
      form.validateFields().then(values => {
        console.log("Form values:", values);
        
        const newMetadata: ProfileMetadata = {
          ...metadata,
          patient_name: values.name,
          patient_gender: values.gender,
          patient_id: values.patient_id,
          patient_dob: values.date_of_birth ? values.date_of_birth.format('YYYY-MM-DD') : undefined
        };
        
        console.log("Submitting new profile with metadata:", newMetadata);
        onCreateNewProfile(newMetadata);
      }).catch(info => {
        console.log('Validate Failed:', info);
      });
    } else if (selectedProfileId) {
      console.log("Confirming association with existing profile:", selectedProfileId);
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
      title="Associate Lab Report with Profile"
      open={visible}
      onCancel={onCancel}
      width={700}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          Skip for Now
        </Button>,
        <Button
          key="submit"
          type="primary"
          loading={loading}
          onClick={handleConfirm}
          disabled={!createNew && !selectedProfileId}
        >
          {createNew ? "Create & Associate" : "Associate"}
        </Button>
      ]}
    >
      {matches.length > 0 && (
        <div className="matches-container">
          <Title level={4}>Potential Profile Matches</Title>
          <p>We found these potential matches based on the lab report information.</p>
          
          <div className="profile-matches">
            {matches.map(match => renderProfileCard(match))}
          </div>
          
          <Divider />
        </div>
      )}
      
      <div className="create-profile-container" style={{ marginTop: 16 }}>
        {matches.length > 0 ? (
          <Button
            type="dashed"
            icon={<PlusCircleOutlined />}
            onClick={handleCreateNew}
            style={{ marginBottom: 16, display: 'block' }}
          >
            Create New Profile Instead
          </Button>
        ) : (
          <Alert
            message="No Matching Profiles Found"
            description="We couldn't find any existing profiles that match this lab report. You can create a new profile below."
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}
        
        {createNew && (
          <Card title="Create New Profile" className={createNew ? '' : 'hidden'}>
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
              <Form.Item
                name="name"
                label="Name"
                rules={[{ required: true, message: 'Please enter a name' }]}
              >
                <Input />
              </Form.Item>
              
              <Form.Item name="date_of_birth" label="Date of Birth">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
              
              <Form.Item name="gender" label="Gender">
                <Select placeholder="Select gender">
                  <Option value="male">Male</Option>
                  <Option value="female">Female</Option>
                  <Option value="other">Other</Option>
                </Select>
              </Form.Item>
              
              <Form.Item name="patient_id" label="Patient ID">
                <Input />
              </Form.Item>
            </Form>
          </Card>
        )}
      </div>
    </Modal>
  );
};

export default ProfileMatchingModal; 
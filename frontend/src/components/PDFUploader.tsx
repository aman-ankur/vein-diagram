import React, { useState } from 'react';
import { Upload, Button, message, Card, Alert, Spin } from 'antd';
import { UploadOutlined, InboxOutlined } from '@ant-design/icons';
import { RcFile } from 'antd/lib/upload';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import ProfileSelector from './ProfileSelector';
import { createProfile } from '../services/profileService';

const { Dragger } = Upload;

interface PDFUploaderProps {
  onUploadSuccess: (fileId: string) => void;
}

const PDFUploader: React.FC<PDFUploaderProps> = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState<boolean>(false);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
  const [profileRequired, setProfileRequired] = useState<boolean>(false);

  const handleProfileSelect = (profileId: string | null) => {
    setSelectedProfileId(profileId);
    if (profileId) {
      setProfileRequired(false);
    }
  };

  const handleCreateProfile = async (
    name: string,
    dateOfBirth?: string,
    gender?: string,
    patientId?: string
  ) => {
    try {
      const newProfile = await createProfile({
        name,
        date_of_birth: dateOfBirth,
        gender,
        patient_id: patientId
      });
      
      setSelectedProfileId(newProfile.id);
      setProfileRequired(false);
      message.success(`Profile "${name}" created successfully`);
    } catch (error) {
      console.error('Error creating profile:', error);
      message.error('Failed to create profile');
    }
  };

  const beforeUpload = (file: RcFile) => {
    // Check if a profile is selected
    if (!selectedProfileId) {
      setProfileRequired(true);
      return false;
    }
    
    // Check file type
    const isPDF = file.type === 'application/pdf';
    if (!isPDF) {
      message.error('You can only upload PDF files!');
      return false;
    }
    
    // Check file size (30MB max)
    const isLt30M = file.size / 1024 / 1024 < 30;
    if (!isLt30M) {
      message.error('File must be smaller than 30MB!');
      return false;
    }
    
    return true;
  };

  const customUpload = async (options: any) => {
    const { file, onSuccess, onError } = options;
    
    // Create form data
    const formData = new FormData();
    formData.append('file', file);
    
    // Add profile_id if selected
    if (selectedProfileId) {
      formData.append('profile_id', selectedProfileId);
    }
    
    setUploading(true);
    
    try {
      // Upload the file
      const response = await axios.post(
        `${API_BASE_URL}/pdf/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      
      setUploading(false);
      onSuccess(response, file);
      
      // Call the success callback with the file ID
      onUploadSuccess(response.data.file_id);
      
      message.success(`${file.name} uploaded successfully`);
    } catch (error) {
      setUploading(false);
      onError(error);
      message.error(`${file.name} upload failed`);
      console.error('Upload error:', error);
    }
  };

  return (
    <Card title="Upload Lab Report PDF">
      <div className="profile-selection-container">
        <h3>Step 1: Select or Create a Profile</h3>
        <ProfileSelector
          selectedProfileId={selectedProfileId}
          onProfileSelect={handleProfileSelect}
          onCreateProfile={handleCreateProfile}
        />
        {profileRequired && (
          <Alert
            message="Profile Required"
            description="Please select or create a profile before uploading a PDF"
            type="warning"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </div>
      
      <div className="upload-container" style={{ marginTop: 24 }}>
        <h3>Step 2: Upload Lab Report</h3>
        <Dragger
          name="file"
          multiple={false}
          beforeUpload={beforeUpload}
          customRequest={customUpload}
          disabled={uploading || !selectedProfileId}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">Click or drag PDF file to this area to upload</p>
          <p className="ant-upload-hint">
            Support for a single PDF file upload. File size limit: 30MB.
          </p>
          {uploading && <Spin tip="Uploading..." />}
        </Dragger>
      </div>
    </Card>
  );
};

export default PDFUploader; 
import React, { useState } from 'react';
import { Upload, Button, message, Card, Alert, Spin } from 'antd';
import { UploadOutlined, InboxOutlined } from '@ant-design/icons';
import { RcFile } from 'antd/lib/upload';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import ProfileSelector from './ProfileSelector';
import ProfileMatchingModal from './ProfileMatchingModal';
import { createProfile } from '../services/profileService';
import { findMatchingProfiles, associatePdfWithProfile, createProfileFromPdf } from '../services/profileService';
import { ProfileMatch, ProfileMetadata, ProfileMatchingResponse } from '../types/Profile';

const { Dragger } = Upload;

interface PDFUploaderProps {
  onUploadSuccess: (fileId: string) => void;
}

const PDFUploader: React.FC<PDFUploaderProps> = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState<boolean>(false);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
  const [profileRequired, setProfileRequired] = useState<boolean>(false);
  
  // States for the smart profile association feature
  const [isMatchingModalVisible, setIsMatchingModalVisible] = useState<boolean>(false);
  const [currentPdfId, setCurrentPdfId] = useState<string | null>(null);
  const [profileMatches, setProfileMatches] = useState<ProfileMatch[]>([]);
  const [extractedMetadata, setExtractedMetadata] = useState<ProfileMetadata>({});
  const [loadingMatches, setLoadingMatches] = useState<boolean>(false);
  const [processingAssociation, setProcessingAssociation] = useState<boolean>(false);

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
    
    // Add profile_id if manually selected from the dropdown
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
      
      // If no profile was manually selected, try smart profile association
      if (!selectedProfileId) {
        setCurrentPdfId(response.data.file_id);
        
        // If metadata is already available in the response, use it
        if (response.data.patient_name || response.data.patient_gender) {
          const metadata: ProfileMetadata = {
            patient_name: response.data.patient_name,
            patient_gender: response.data.patient_gender,
            patient_id: response.data.patient_id,
            lab_name: response.data.lab_name,
            report_date: response.data.report_date
          };
          
          setExtractedMetadata(metadata);
          findMatches(response.data.file_id);
        } else {
          // Wait a moment to allow the server to extract metadata
          setTimeout(() => findMatches(response.data.file_id), 1000);
        }
      } else {
        // Call the success callback with the file ID if a profile was manually selected
        onUploadSuccess(response.data.file_id);
      }
      
      message.success(`${file.name} uploaded successfully`);
    } catch (error) {
      setUploading(false);
      onError(error);
      message.error(`${file.name} upload failed`);
      console.error('Upload error:', error);
    }
  };
  
  const findMatches = async (pdfId: string) => {
    setLoadingMatches(true);
    try {
      const result: ProfileMatchingResponse = await findMatchingProfiles(pdfId);
      setProfileMatches(result.matches || []);
      setExtractedMetadata(result.metadata || {});
      setIsMatchingModalVisible(true);
    } catch (error) {
      console.error('Error finding matching profiles:', error);
      message.error('Failed to find matching profiles');
      // Fall back to default behavior - just pass the fileId back
      onUploadSuccess(pdfId);
    } finally {
      setLoadingMatches(false);
    }
  };
  
  const handleSelectExistingProfile = async (profileId: string) => {
    if (!currentPdfId) return;
    
    setProcessingAssociation(true);
    try {
      await associatePdfWithProfile(currentPdfId, profileId);
      message.success('Lab report associated with profile successfully');
      setIsMatchingModalVisible(false);
      onUploadSuccess(currentPdfId);
    } catch (error) {
      console.error('Error associating PDF with profile:', error);
      message.error('Failed to associate lab report with profile');
    } finally {
      setProcessingAssociation(false);
    }
  };
  
  const handleCreateNewProfile = async (metadata: ProfileMetadata) => {
    if (!currentPdfId) return;
    
    setProcessingAssociation(true);
    try {
      await createProfileFromPdf(currentPdfId, metadata);
      message.success('New profile created and lab report associated successfully');
      setIsMatchingModalVisible(false);
      onUploadSuccess(currentPdfId);
    } catch (error) {
      console.error('Error creating new profile:', error);
      message.error('Failed to create new profile');
    } finally {
      setProcessingAssociation(false);
    }
  };
  
  const handleCancelMatching = () => {
    setIsMatchingModalVisible(false);
    // If the user cancels, still proceed with the upload
    if (currentPdfId) {
      onUploadSuccess(currentPdfId);
    }
  };

  return (
    <Card title="Upload Lab Report PDF">
      <div className="profile-selection-container">
        <h3>Step 1: Select a Profile (Optional)</h3>
        <p>If you want to manually select a profile, you can do so here. Otherwise, we'll help you match after upload.</p>
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
          disabled={uploading}
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
      
      {/* Profile Matching Modal */}
      <ProfileMatchingModal
        visible={isMatchingModalVisible}
        pdfId={currentPdfId || ''}
        matches={profileMatches}
        metadata={extractedMetadata}
        onCancel={handleCancelMatching}
        onSelectProfile={handleSelectExistingProfile}
        onCreateNewProfile={handleCreateNewProfile}
        loading={processingAssociation}
      />
    </Card>
  );
};

export default PDFUploader; 
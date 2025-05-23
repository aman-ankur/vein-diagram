import React, { useState, useEffect } from 'react';
import { Upload, message, Card, Alert, Spin } from 'antd'; // Removed Button
import { InboxOutlined } from '@ant-design/icons'; // Removed UploadOutlined
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
  initialFileId?: string;
}

const PDFUploader: React.FC<PDFUploaderProps> = ({ onUploadSuccess, initialFileId }) => {
  const [uploading, setUploading] = useState<boolean>(false);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
  const [profileRequired, setProfileRequired] = useState<boolean>(false);
  
  // States for the smart profile association feature
  const [isMatchingModalVisible, setIsMatchingModalVisible] = useState<boolean>(false);
  const [currentPdfId, setCurrentPdfId] = useState<string | null>(initialFileId || null);
  const [profileMatches, setProfileMatches] = useState<ProfileMatch[]>([]);
  const [extractedMetadata, setExtractedMetadata] = useState<ProfileMetadata>({});
  // const [loadingMatches, setLoadingMatches] = useState<boolean>(false); // Removed unused state
  const [processingAssociation, setProcessingAssociation] = useState<boolean>(false);

  // If initialFileId is provided, trigger profile matching immediately
  useEffect(() => {
    if (initialFileId && !isMatchingModalVisible && !selectedProfileId) {
      findMatches(initialFileId);
    }
  }, [initialFileId]);

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
        `${API_BASE_URL}/api/pdf/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      
      setUploading(false);
      onSuccess(response, file);
      
      // Always call the success callback with the file ID first
      // This ensures the facts carousel processing step is shown
      onUploadSuccess(response.data.file_id);
      
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
          // Wait a moment to allow the server to extract metadata and begin processing
          // Then trigger profile matching
          setTimeout(() => findMatches(response.data.file_id), 2000);
        }
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
    console.log("Starting profile matching for PDF:", pdfId);
    // setLoadingMatches(true); // Removed usage of unused state
    try {
      // Wait until the PDF is fully processed
      let statusCheckAttempts = 0;
      const maxAttempts = 300; // Increased: 300 attempts * 2 sec = 600 seconds (10 minutes) max wait time

      // Check if the PDF has been processed before attempting to match profiles
      const checkPdfProcessed = async (): Promise<boolean> => {
        try {
          const response = await axios.get(`${API_BASE_URL}/api/pdf/status/${pdfId}`);
          console.log("PDF processing status:", response.data.status);
          
          // If the PDF has been processed, we can proceed with matching
          if (response.data.status === "processed" || response.data.status === "completed") {
            return true;
          }
          
          // If it's still processing and we haven't hit max attempts, try again
          if ((response.data.status === "processing" || response.data.status === "pending") && statusCheckAttempts < maxAttempts) {
            return false;
          }
          
          // If the PDF has an error status, throw an error
          if (response.data.status === "error" || response.data.status === "failed") {
            throw new Error(`PDF processing failed: ${response.data.error_message || "Unknown error"}`);
          }
          
          // If max attempts reached, give up
          if (statusCheckAttempts >= maxAttempts) {
            throw new Error("PDF processing timed out after multiple attempts");
          }
          
          return false;
        } catch (error) {
          console.error("Error checking PDF status:", error);
          
          // Only throw if we've reached max attempts, otherwise continue trying
          if (statusCheckAttempts >= maxAttempts) {
            throw error;
          }
          return false;
        }
      };

      // --- Start Polling Logic ---
      let isProcessed = false;

      // **Initial Status Check**
      try {
        console.log(`Performing initial status check for PDF: ${pdfId}`);
        const initialStatusResponse = await axios.get(`${API_BASE_URL}/api/pdf/status/${pdfId}`);
        const initialStatus = initialStatusResponse.data.status;
        console.log(`Initial status for PDF ${pdfId}: ${initialStatus}`);

        if (initialStatus === "processed" || initialStatus === "completed") {
          console.log(`PDF ${pdfId} already processed. Skipping polling.`);
          isProcessed = true; // Mark as processed to proceed directly to matching
        } else if (initialStatus === "error" || initialStatus === "failed") {
          console.error(`PDF ${pdfId} processing failed previously. Aborting.`);
          throw new Error(`PDF processing failed previously: ${initialStatusResponse.data.error_message || "Unknown error"}`);
        }
        // Otherwise, status is 'pending' or 'processing', so continue to polling loop
      } catch (initialError) {
         console.error(`Error during initial status check for PDF ${pdfId}:`, initialError);
         // If initial check fails, proceed to polling loop as a fallback,
         // but log the error. The loop's error handling will take over.
      }


      // **Polling Loop (only if not already processed/failed)**
      while (!isProcessed && statusCheckAttempts < maxAttempts) {
        statusCheckAttempts++;
        try {
          isProcessed = await checkPdfProcessed();
          
          if (isProcessed) {
            console.log("PDF is processed, proceeding to profile matching");
            break;
          }
          
          // Wait for 2 seconds before checking again
          console.log(`PDF still processing, waiting before checking again (attempt ${statusCheckAttempts}/${maxAttempts})`);
          await new Promise(resolve => setTimeout(resolve, 2000));
        } catch (error) {
          // Log error but continue trying until max attempts
          console.error(`Error during status check attempt ${statusCheckAttempts}:`, error);
          if (statusCheckAttempts >= maxAttempts) {
            throw error;
          }
          // Wait a bit longer after an error
          await new Promise(resolve => setTimeout(resolve, 3000));
        }
      }
      
      // If polling finished but PDF is still not processed (e.g., initial check failed and loop timed out)
      if (!isProcessed && statusCheckAttempts >= maxAttempts) {
        throw new Error("PDF processing timed out after multiple attempts.");
      }

      // --- Profile Matching (only if processed) ---
      if (isProcessed) {
          console.log("Calling profile matching API for PDF:", pdfId);
          const result: ProfileMatchingResponse = await findMatchingProfiles(pdfId);
          console.log("Profile matching results:", result);

          // If we have valid results, show the modal
          setProfileMatches(result.matches || []);
          setExtractedMetadata(result.metadata || {});

          // Always show the matching modal, even if no matches are found
          // In that case, it will default to the "Create New Profile" option
          console.log("Showing profile matching modal");
          setIsMatchingModalVisible(true);
      } else {
           // This case should ideally not be reached if timeout error is thrown correctly
           console.error(`Polling loop finished for PDF ${pdfId} but it was not marked as processed.`);
           message.error("PDF processing check completed, but status is unclear. Please check manually.");
           onUploadSuccess(pdfId); // Fallback
      }


    } catch (error) { // This catch block handles errors from the entire process (initial check, polling, matching API call)
      console.error('Error finding matching profiles:', error);
      // Display the error message from the exception if available
      const errorMessage = error instanceof Error ? error.message : 'Failed to find matching profiles or process PDF.';
      message.error(errorMessage + ' Using default profile.');

      // Fall back to default behavior - just pass the fileId back
      // In a production app, we might want to offer a retry option
      onUploadSuccess(pdfId);
    } finally {
      // setLoadingMatches(false); // Removed usage of unused state
    }
  };
  
  const handleSelectExistingProfile = async (profileId: string) => {
    if (!currentPdfId) return;
    
    setProcessingAssociation(true);
    try {
      const profile = await associatePdfWithProfile(currentPdfId, profileId);
      message.success('Lab report associated with profile successfully');
      setIsMatchingModalVisible(false);
      // Pass back both the fileId and profileId
      onUploadSuccess(`${currentPdfId}?profileId=${profile.id}`);
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
      const profile = await createProfileFromPdf(currentPdfId, metadata);
      message.success('New profile created and lab report associated successfully');
      setIsMatchingModalVisible(false);
      // Pass back both the fileId and profileId
      onUploadSuccess(`${currentPdfId}?profileId=${profile.id}`);
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
      // Just pass the fileId without a profileId
      onUploadSuccess(currentPdfId);
    }
  };

  return (
    <Card title="Upload Lab Report PDF">
      <div className="profile-selection-container">
        <h3>Step 1: Select a Profile (Optional)</h3>
        <p>If you want to manually select a profile, you can do so here. Otherwise, we'll help you match the lab report to a profile after upload.</p>
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
        <p>After uploading, the system will extract biomarkers and help you associate them with the right profile.</p>
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
            Support for a single PDF file upload. File size limit: 30MB. Note: Only the first 3 pages will be processed.
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

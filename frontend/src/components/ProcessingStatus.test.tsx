// React import removed - unused
import { render, screen } from '@testing-library/react';
import ProcessingStatus from './ProcessingStatus';

describe('ProcessingStatus Component', () => {
  it('renders nothing when status is null', () => {
    const { container } = render(<ProcessingStatus status={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders pending status correctly', () => {
    render(<ProcessingStatus status="pending" />);
    expect(screen.getByText(/your file is in the queue/i)).toBeInTheDocument();
  });

  it('renders processing status correctly', () => {
    render(<ProcessingStatus status="processing" />);
    expect(screen.getByText(/processing your lab report/i)).toBeInTheDocument();
  });

  it('renders completed status correctly', () => {
    render(<ProcessingStatus status="completed" />);
    expect(screen.getByText(/processing completed successfully/i)).toBeInTheDocument();
  });

  it('renders error status with default message', () => {
    render(<ProcessingStatus status="error" />);
    expect(screen.getByText(/an error occurred/i)).toBeInTheDocument();
  });

  it('renders error status with custom message', () => {
    render(<ProcessingStatus status="error" errorMessage="Custom error message" />);
    expect(screen.getByText(/custom error message/i)).toBeInTheDocument();
  });

  it('renders timeout status correctly', () => {
    render(<ProcessingStatus status="timeout" />);
    expect(screen.getByText(/taking longer than expected/i)).toBeInTheDocument();
  });
});

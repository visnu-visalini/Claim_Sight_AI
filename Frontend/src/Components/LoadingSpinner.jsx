import React from 'react';
import './LoadingSpinner.css';

export default function LoadingSpinner() {
  return (
    <div className="spinner-overlay" data-testid="loading-spinner">
      <div className="spinner" />
    </div>
  );
}


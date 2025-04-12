'use client';

import React from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';

export default function DataPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <div className="min-h-screen bg-white">
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="border-4 border-dashed border-black rounded-lg h-96 p-4">
              <h1 className="text-2xl font-bold text-black mb-4">Data Management</h1>
              <p className="text-black">This page is accessible only to admin users.</p>
              {/* Add your data management components here */}
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
} 
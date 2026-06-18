"use client";

import React, { useEffect, useState } from 'react';

interface PdfReviewerProps {
  pdfUrl: string;
  reportId: number;
  initialAnnotations?: any[];
  onSave?: (annotations: any[]) => void;
  readOnly?: boolean;
}

export function PdfReviewer(props: PdfReviewerProps) {
  const [Component, setComponent] = useState<any>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      import('./PdfReviewerInner').then(mod => {
        setComponent(() => mod.PdfReviewerInner);
      }).catch(err => {
        console.error("Failed to load PdfReviewer", err);
      });
    }
  }, []);

  if (!Component) {
    return <div className="p-4 text-center text-gray-500 border rounded min-h-[500px] flex items-center justify-center bg-gray-50">កំពុងទាញយកកម្មវិធីអាន PDF...</div>;
  }

  return <Component {...props} />;
}

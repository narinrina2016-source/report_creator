"use client";

import React, { useMemo, useEffect, useState } from 'react';
import 'react-quill-new/dist/quill.snow.css';

interface QuillEditorProps {
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export default function QuillEditor({ value, onChange, className }: QuillEditorProps) {
  const [ReactQuill, setReactQuill] = useState<any>(null);
  const [QuillLib, setQuillLib] = useState<any>(null);
  const [isModuleLoaded, setIsModuleLoaded] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      Promise.all([
        import('react-quill-new'),
        import('quill-image-resize-module-react')
      ]).then(([QuillModule, ImageResizeModule]) => {
        const { default: RQ, Quill } = QuillModule;
        Quill.register('modules/imageResize', ImageResizeModule.default);
        setReactQuill(() => RQ);
        setQuillLib(Quill);
        setIsModuleLoaded(true);
      }).catch(err => {
        console.error("Failed to load Quill modules", err);
      });
    }
  }, []);

  const modules = useMemo(() => {
    if (!isModuleLoaded || !QuillLib) return { toolbar: false };
    return {
      toolbar: [
        [{ 'header': [1, 2, 3, false] }],
        ['bold', 'italic', 'underline', 'strike'],
        [{ 'color': [] }, { 'background': [] }],
        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
        [{ 'align': [] }],
        ['image'],
        ['clean']
      ],
      imageResize: {
        parchment: QuillLib.import('parchment'),
        modules: [ 'Resize', 'DisplaySize' ]
      }
    };
  }, [isModuleLoaded, QuillLib]);

  if (!ReactQuill || !isModuleLoaded) {
    return <div className="p-4 text-center text-gray-500 border rounded min-h-[200px] flex items-center justify-center">កំពុងទាញយកកម្មវិធីកែសម្រួល...</div>;
  }

  return (
    <ReactQuill 
      theme="snow" 
      value={value} 
      onChange={onChange}
      className={className}
      modules={modules}
    />
  );
}

import re

with open('frontend/src/app/reports/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add Supabase import at the top
if 'from "@/lib/supabase"' not in content:
    content = content.replace('import { CheckCircle', 'import { supabase } from "@/lib/supabase";\nimport { CheckCircle')

# Add file upload state inside ReportsPage
state_add = """
  // PDF Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
"""
content = re.sub(r'(const \[editingReportId, setEditingReportId\] = useState<number \| null>\(null\);)', r'\1' + state_add, content)

# Rewrite handleGenerate to handle PDF upload instead of template data
new_handle_generate = """
  const handleGenerate = async () => {
    if (!reportTitle || !selectedTemplateId) {
      alert("Please enter title and select a category");
      return;
    }
    setIsGenerating(true);
    try {
      let pdfUrl = "";
      if (selectedFile) {
        const fileExt = selectedFile.name.split('.').pop();
        const fileName = `${Math.random()}.${fileExt}`;
        const filePath = `${fileName}`;
        
        const { error: uploadError, data } = await supabase.storage
          .from('reports')
          .upload(filePath, selectedFile);
          
        if (uploadError) {
          throw uploadError;
        }
        
        const { data: publicUrlData } = supabase.storage
          .from('reports')
          .getPublicUrl(filePath);
          
        pdfUrl = publicUrlData.publicUrl;
      }

      const payload = {
        title: reportTitle,
        template_id: parseInt(selectedTemplateId),
        data: formData,
        pdf_url: pdfUrl || (editingReportId ? undefined : null) // Keep old URL if editing and no new file
      };
      
      const url = editingReportId 
        ? `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/reports/${editingReportId}`
        : `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/reports/`;
        
      const res = await fetch(url, {
        method: editingReportId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setIsModalOpen(false);
        setReportTitle("");
        setSelectedTemplateId("");
        setSelectedFile(null);
        setFormData({});
        setEditingReportId(null);
        fetchReports();
      } else {
        const errData = await res.json();
        alert(`Failed to save report: ${errData.detail || 'Unknown error'}`);
      }
    } catch (e) {
      console.error(e);
      alert("Error saving report or uploading file");
    } finally {
      setIsGenerating(false);
    }
  };
"""
content = re.sub(r'const handleGenerate = async \(\) => \{.*?\n  \};\n', new_handle_generate, content, flags=re.DOTALL)

# Replace the dynamicFields UI with file upload input
# Find the start of {dynamicFields.length > 0 && (
dynamic_fields_pattern = r'\{dynamicFields\.length > 0 && \(\s*<div className="mt-6 pt-4 border-t border-gray-200">.*?</div>\s*\)\}'
upload_ui = """
              <div className="mt-6 pt-4 border-t border-gray-200">
                <h4 className="text-sm font-bold text-gray-900 mb-3">បង្ហោះឯកសារ PDF (Upload PDF Document)</h4>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">ជ្រើសរើសឯកសារ (.pdf)</label>
                    <input 
                      type="file" 
                      accept="application/pdf"
                      onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2 text-sm"
                    />
                    {editingReportId && <p className="text-xs text-gray-500 mt-1">ទុកចោលបើមិនចង់ប្តូរឯកសារថ្មី</p>}
                  </div>
                </div>
              </div>
"""
content = re.sub(dynamic_fields_pattern, upload_ui, content, flags=re.DOTALL)

with open('frontend/src/app/reports/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")

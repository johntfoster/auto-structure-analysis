import { useState } from 'react'

export default function Capture() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Capture Structure</h1>
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
        <p className="text-gray-600 mb-4">
          Upload a photo of a truss structure for analysis
        </p>
        <input
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="block mx-auto mb-4"
        />
        {selectedFile && (
          <p className="text-sm text-gray-500">
            Selected: {selectedFile.name}
          </p>
        )}
      </div>
    </div>
  )
}

import { useParams } from 'react-router-dom'

export default function Analyze() {
  const { id } = useParams<{ id: string }>()

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Analysis Results</h1>
      <div className="bg-gray-100 rounded-lg p-8">
        <p className="text-gray-600">
          Displaying analysis for structure ID: {id}
        </p>
        <p className="text-sm text-gray-500 mt-4">
          3D visualization and structural analysis results will appear here.
        </p>
      </div>
    </div>
  )
}

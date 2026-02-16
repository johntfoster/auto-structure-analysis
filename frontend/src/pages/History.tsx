import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { getHistory, type HistoryItem } from '../services/api'

export default function History() {
  const { data: history, isLoading, error } = useQuery<HistoryItem[]>({
    queryKey: ['history'],
    queryFn: getHistory,
  })

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Analysis History</h1>
        <div className="flex items-center justify-center h-64">
          <div className="text-xl text-gray-600">⏳ Loading history...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Analysis History</h1>
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Failed to load history. Please try again.
        </div>
      </div>
    )
  }

  if (!history || history.length === 0) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Analysis History</h1>
        <div className="bg-gray-50 rounded-lg p-12 text-center">
          <div className="mb-4">
            <svg className="mx-auto h-24 w-24 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">
            No analyses yet
          </h2>
          <p className="text-gray-600 mb-6">
            Your structural analysis history will appear here once you capture and analyze your first structure.
          </p>
          <Link
            to="/capture"
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition inline-block"
          >
            Capture Your First Structure
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Analysis History</h1>
        <Link
          to="/capture"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition"
        >
          + New Analysis
        </Link>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {history.map((item) => (
          <Link
            key={item.id}
            to={`/analyze/${item.id}`}
            className="bg-white rounded-lg shadow hover:shadow-lg transition overflow-hidden group"
          >
            {/* Thumbnail */}
            <div className="aspect-video bg-gray-200 overflow-hidden">
              {item.thumbnail_url ? (
                <img
                  src={item.thumbnail_url}
                  alt={`Analysis ${item.id}`}
                  className="w-full h-full object-cover group-hover:scale-105 transition"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              )}
            </div>

            {/* Card Content */}
            <div className="p-4">
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-lg text-gray-900 group-hover:text-blue-600 transition">
                  {item.structure_type}
                </h3>
                <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded">
                  {item.member_count} members
                </span>
              </div>
              
              <p className="text-sm text-gray-600">
                {new Date(item.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>

              <div className="mt-3 text-blue-600 text-sm font-medium group-hover:underline">
                View Results →
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

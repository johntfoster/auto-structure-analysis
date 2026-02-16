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
      <div className="max-w-6xl mx-auto px-4 py-6 sm:py-8">
        <h1 className="text-2xl sm:text-3xl font-bold mb-4 sm:mb-6 text-gray-900 dark:text-white">Analysis History</h1>
        <div className="flex items-center justify-center h-64">
          <div className="text-lg sm:text-xl text-gray-600 dark:text-gray-400">⏳ Loading history...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-6 sm:py-8">
        <h1 className="text-2xl sm:text-3xl font-bold mb-4 sm:mb-6 text-gray-900 dark:text-white">Analysis History</h1>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded text-sm sm:text-base">
          Failed to load history. Please try again.
        </div>
      </div>
    )
  }

  if (!history || history.length === 0) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-6 sm:py-8">
        <h1 className="text-2xl sm:text-3xl font-bold mb-4 sm:mb-6 text-gray-900 dark:text-white">Analysis History</h1>
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-8 sm:p-12 text-center">
          <div className="mb-4">
            <svg className="mx-auto h-16 sm:h-24 w-16 sm:w-24 text-gray-400 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h2 className="text-lg sm:text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
            No analyses yet
          </h2>
          <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 mb-6">
            Your structural analysis history will appear here once you capture and analyze your first structure.
          </p>
          <Link
            to="/capture"
            className="bg-blue-600 dark:bg-blue-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 dark:hover:bg-blue-600 transition inline-block touch-manipulation min-h-[44px]"
          >
            Capture Your First Structure
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 sm:py-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 sm:mb-6 gap-3">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">Analysis History</h1>
        <Link
          to="/capture"
          className="bg-blue-600 dark:bg-blue-500 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 dark:hover:bg-blue-600 transition touch-manipulation min-h-[44px]"
        >
          + New Analysis
        </Link>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {history.map((item) => (
          <Link
            key={item.id}
            to={`/analyze/${item.id}`}
            className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg dark:shadow-gray-900/50 transition overflow-hidden group"
          >
            {/* Thumbnail */}
            <div className="aspect-video bg-gray-200 dark:bg-gray-700 overflow-hidden">
              {item.thumbnail_url ? (
                <img
                  src={item.thumbnail_url}
                  alt={`Analysis ${item.id}`}
                  className="w-full h-full object-cover group-hover:scale-105 transition"
                  loading="lazy"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400 dark:text-gray-600">
                  <svg className="w-12 sm:w-16 h-12 sm:h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              )}
            </div>

            {/* Card Content */}
            <div className="p-3 sm:p-4">
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-base sm:text-lg text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition truncate">
                  {item.structure_type}
                </h3>
                <span className="bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs font-semibold px-2 py-1 rounded ml-2 whitespace-nowrap">
                  {item.member_count} members
                </span>
              </div>
              
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                {new Date(item.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>

              <div className="mt-3 text-blue-600 dark:text-blue-400 text-sm font-medium group-hover:underline">
                View Results →
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

import type { EditorMode } from '../types/model'

interface EditorToolbarProps {
  mode: EditorMode
  onModeChange: (mode: EditorMode) => void
  canUndo: boolean
  canRedo: boolean
  onUndo: () => void
  onRedo: () => void
  onZoomIn: () => void
  onZoomOut: () => void
  onFitToView: () => void
  onAnalyze: () => void
}

export default function EditorToolbar({
  mode,
  onModeChange,
  canUndo,
  canRedo,
  onUndo,
  onRedo,
  onZoomIn,
  onZoomOut,
  onFitToView,
  onAnalyze,
}: EditorToolbarProps) {
  const modeButtons: Array<{ mode: EditorMode; label: string; icon: string }> = [
    { mode: 'select', label: 'Select', icon: '👆' },
    { mode: 'add-node', label: 'Add Node', icon: '➕' },
    { mode: 'add-member', label: 'Add Member', icon: '📏' },
    { mode: 'add-load', label: 'Add Load', icon: '⬇️' },
    { mode: 'delete', label: 'Delete', icon: '🗑️' },
  ]

  return (
    <div className="bg-white border-b shadow-sm px-4 py-3">
      <div className="flex flex-wrap items-center gap-2">
        {/* Mode buttons */}
        <div className="flex gap-1 border-r pr-3">
          {modeButtons.map((btn) => (
            <button
              key={btn.mode}
              onClick={() => onModeChange(btn.mode)}
              className={`px-3 py-2 rounded text-sm font-medium transition ${
                mode === btn.mode
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
              title={btn.label}
            >
              <span className="mr-1">{btn.icon}</span>
              <span className="hidden sm:inline">{btn.label}</span>
            </button>
          ))}
        </div>

        {/* Undo/Redo */}
        <div className="flex gap-1 border-r pr-3">
          <button
            onClick={onUndo}
            disabled={!canUndo}
            className="px-3 py-2 rounded text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition"
            title="Undo (Ctrl+Z)"
          >
            ↶
          </button>
          <button
            onClick={onRedo}
            disabled={!canRedo}
            className="px-3 py-2 rounded text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition"
            title="Redo (Ctrl+Shift+Z)"
          >
            ↷
          </button>
        </div>

        {/* Zoom controls */}
        <div className="flex gap-1 border-r pr-3">
          <button
            onClick={onZoomIn}
            className="px-3 py-2 rounded text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition"
            title="Zoom In"
          >
            🔍+
          </button>
          <button
            onClick={onZoomOut}
            className="px-3 py-2 rounded text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition"
            title="Zoom Out"
          >
            🔍−
          </button>
          <button
            onClick={onFitToView}
            className="px-3 py-2 rounded text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition"
            title="Fit to View"
          >
            ⊡
          </button>
        </div>

        {/* Analyze button */}
        <button
          onClick={onAnalyze}
          className="ml-auto px-6 py-2 rounded-lg text-sm font-semibold bg-blue-600 text-white hover:bg-blue-700 transition"
        >
          🔍 Analyze
        </button>
      </div>
    </div>
  )
}

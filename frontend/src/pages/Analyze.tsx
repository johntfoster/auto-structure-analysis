import { useParams, Link } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { getAnalysis, reanalyze, type AnalysisResult } from '../services/api'
import ModelEditor from '../components/ModelEditor'
import ResultsVisualization from '../components/ResultsVisualization'
import type { StructuralModel } from '../types/model'

export default function Analyze() {
  const { id } = useParams<{ id: string }>()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  
  const [selectedMaterial, setSelectedMaterial] = useState<string>('steel')
  const [newLoad, setNewLoad] = useState({ nodeId: '', fx: '', fy: '' })
  const [loads, setLoads] = useState<Array<{ node_id: number; fx: number; fy: number }>>([])
  const [showEditor, setShowEditor] = useState(false)
  const [editableModel, setEditableModel] = useState<StructuralModel | null>(null)
  const [showDeformed, setShowDeformed] = useState(false)
  const [showStress, setShowStress] = useState(true)
  const [showForces, setShowForces] = useState(true)
  const [deformationScale, setDeformationScale] = useState(50)

  const { data: analysis, isLoading, error, refetch } = useQuery<AnalysisResult>({
    queryKey: ['analysis', id],
    queryFn: () => getAnalysis(id!),
    enabled: !!id,
  })

  const reanalyzeMutation = useMutation({
    mutationFn: (updates: { material?: string; loads?: Array<{ node_id: number; fx: number; fy: number }> }) =>
      reanalyze(id!, updates),
    onSuccess: () => {
      refetch()
    },
  })

  // Initialize loads from analysis data
  useEffect(() => {
    if (analysis?.loads) {
      setLoads(analysis.loads)
    }
    
    // Initialize editable model from analysis
    if (analysis) {
      const model: StructuralModel = {
        nodes: analysis.nodes.map(n => ({
          id: n.id.toString(),
          x: n.x,
          y: n.y,
          support: n.support_type || 'none',
          loads: undefined,
        })),
        members: analysis.members.map(m => ({
          id: m.id.toString(),
          startNodeId: m.start_node.toString(),
          endNodeId: m.end_node.toString(),
          material: selectedMaterial,
        })),
      }
      setEditableModel(model)
    }
  }, [analysis, selectedMaterial])

  // Draw visualization
  useEffect(() => {
    if (analysis && canvasRef.current) {
      drawStructure(analysis)
    }
  }, [analysis])

  const drawStructure = (data: AnalysisResult) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size
    const containerWidth = canvas.parentElement?.clientWidth || 800
    canvas.width = containerWidth
    canvas.height = 600

    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Calculate bounds
    const nodes = data.nodes
    if (nodes.length === 0) return

    const xs = nodes.map(n => n.x)
    const ys = nodes.map(n => n.y)
    const minX = Math.min(...xs)
    const maxX = Math.max(...xs)
    const minY = Math.min(...ys)
    const maxY = Math.max(...ys)

    const rangeX = maxX - minX || 1
    const rangeY = maxY - minY || 1

    // Add padding
    const padding = 80
    const scaleX = (canvas.width - 2 * padding) / rangeX
    const scaleY = (canvas.height - 2 * padding) / rangeY
    const scale = Math.min(scaleX, scaleY)

    // Transform function
    const transform = (x: number, y: number): [number, number] => {
      const tx = padding + (x - minX) * scale
      const ty = canvas.height - (padding + (y - minY) * scale) // Flip Y axis
      return [tx, ty]
    }

    // Draw members
    data.members.forEach(member => {
      const startNode = nodes.find(n => n.id === member.start_node)
      const endNode = nodes.find(n => n.id === member.end_node)
      
      if (startNode && endNode) {
        const [x1, y1] = transform(startNode.x, startNode.y)
        const [x2, y2] = transform(endNode.x, endNode.y)

        // Determine color based on force
        let color = '#6B7280' // gray for zero force
        if (Math.abs(member.axial_force) > 0.01) {
          color = member.axial_force > 0 ? '#EF4444' : '#3B82F6' // red for tension, blue for compression
        }

        // Line thickness proportional to force magnitude
        const maxForce = Math.max(...data.members.map(m => Math.abs(m.axial_force)), 1)
        const lineWidth = Math.max(2, Math.min(10, (Math.abs(member.axial_force) / maxForce) * 8 + 2))

        ctx.strokeStyle = color
        ctx.lineWidth = lineWidth
        ctx.beginPath()
        ctx.moveTo(x1, y1)
        ctx.lineTo(x2, y2)
        ctx.stroke()

        // Draw member force label at midpoint
        const midX = (x1 + x2) / 2
        const midY = (y1 + y2) / 2
        ctx.fillStyle = color
        ctx.font = 'bold 11px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(`${member.axial_force.toFixed(1)}k`, midX, midY - 5)
      }
    })

    // Draw loads
    data.loads.forEach(load => {
      const node = nodes.find(n => n.id === load.node_id)
      if (node) {
        const [x, y] = transform(node.x, node.y)
        
        // Draw load arrows
        const arrowScale = 30
        if (Math.abs(load.fx) > 0.01) {
          drawArrow(ctx, x, y, x + load.fx * arrowScale, y, '#F59E0B', 3)
        }
        if (Math.abs(load.fy) > 0.01) {
          drawArrow(ctx, x, y, x, y - load.fy * arrowScale, '#F59E0B', 3)
        }
      }
    })

    // Draw nodes and supports
    nodes.forEach(node => {
      const [x, y] = transform(node.x, node.y)

      // Draw support symbols
      if (node.support_type === 'pin') {
        drawPinSupport(ctx, x, y)
      } else if (node.support_type === 'roller') {
        drawRollerSupport(ctx, x, y)
      }

      // Draw node circle
      ctx.fillStyle = '#1F2937'
      ctx.beginPath()
      ctx.arc(x, y, 6, 0, Math.PI * 2)
      ctx.fill()

      // Draw node label
      ctx.fillStyle = '#1F2937'
      ctx.font = 'bold 12px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(`${node.id}`, x, y - 12)

      // Draw reactions if present
      if (node.reaction_x || node.reaction_y) {
        ctx.fillStyle = '#059669'
        ctx.font = '10px sans-serif'
        const rxText = node.reaction_x ? `Rx:${node.reaction_x.toFixed(1)}` : ''
        const ryText = node.reaction_y ? `Ry:${node.reaction_y.toFixed(1)}` : ''
        ctx.fillText(`${rxText} ${ryText}`, x, y + 20)
      }
    })

    // Add legend
    drawLegend(ctx, canvas.width - 150, 20)
  }

  const drawArrow = (
    ctx: CanvasRenderingContext2D,
    x1: number,
    y1: number,
    x2: number,
    y2: number,
    color: string,
    width: number
  ) => {
    const headlen = 10
    const dx = x2 - x1
    const dy = y2 - y1
    const angle = Math.atan2(dy, dx)

    ctx.strokeStyle = color
    ctx.fillStyle = color
    ctx.lineWidth = width

    // Draw line
    ctx.beginPath()
    ctx.moveTo(x1, y1)
    ctx.lineTo(x2, y2)
    ctx.stroke()

    // Draw arrowhead
    ctx.beginPath()
    ctx.moveTo(x2, y2)
    ctx.lineTo(
      x2 - headlen * Math.cos(angle - Math.PI / 6),
      y2 - headlen * Math.sin(angle - Math.PI / 6)
    )
    ctx.lineTo(
      x2 - headlen * Math.cos(angle + Math.PI / 6),
      y2 - headlen * Math.sin(angle + Math.PI / 6)
    )
    ctx.closePath()
    ctx.fill()
  }

  const drawPinSupport = (ctx: CanvasRenderingContext2D, x: number, y: number) => {
    ctx.fillStyle = '#059669'
    ctx.strokeStyle = '#059669'
    ctx.lineWidth = 2
    
    // Draw triangle
    ctx.beginPath()
    ctx.moveTo(x, y)
    ctx.lineTo(x - 12, y + 20)
    ctx.lineTo(x + 12, y + 20)
    ctx.closePath()
    ctx.fill()
  }

  const drawRollerSupport = (ctx: CanvasRenderingContext2D, x: number, y: number) => {
    ctx.fillStyle = '#059669'
    ctx.strokeStyle = '#059669'
    ctx.lineWidth = 2
    
    // Draw triangle
    ctx.beginPath()
    ctx.moveTo(x, y)
    ctx.lineTo(x - 12, y + 20)
    ctx.lineTo(x + 12, y + 20)
    ctx.closePath()
    ctx.fill()
    
    // Draw circles (wheels)
    ctx.beginPath()
    ctx.arc(x - 8, y + 25, 4, 0, Math.PI * 2)
    ctx.fill()
    ctx.beginPath()
    ctx.arc(x + 8, y + 25, 4, 0, Math.PI * 2)
    ctx.fill()
  }

  const drawLegend = (ctx: CanvasRenderingContext2D, x: number, y: number) => {
    ctx.font = 'bold 12px sans-serif'
    ctx.fillStyle = '#1F2937'
    ctx.textAlign = 'left'
    ctx.fillText('Legend:', x, y)

    // Tension
    ctx.strokeStyle = '#EF4444'
    ctx.lineWidth = 3
    ctx.beginPath()
    ctx.moveTo(x, y + 15)
    ctx.lineTo(x + 30, y + 15)
    ctx.stroke()
    ctx.fillStyle = '#1F2937'
    ctx.font = '11px sans-serif'
    ctx.fillText('Tension', x + 35, y + 18)

    // Compression
    ctx.strokeStyle = '#3B82F6'
    ctx.lineWidth = 3
    ctx.beginPath()
    ctx.moveTo(x, y + 30)
    ctx.lineTo(x + 30, y + 30)
    ctx.stroke()
    ctx.fillText('Compression', x + 35, y + 33)

    // Zero force
    ctx.strokeStyle = '#6B7280'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(x, y + 45)
    ctx.lineTo(x + 30, y + 45)
    ctx.stroke()
    ctx.fillText('Zero Force', x + 35, y + 48)
  }

  const handleMaterialChange = (material: string) => {
    setSelectedMaterial(material)
    reanalyzeMutation.mutate({ material, loads })
  }

  const handleAddLoad = () => {
    if (newLoad.nodeId && (newLoad.fx || newLoad.fy)) {
      const load = {
        node_id: parseInt(newLoad.nodeId),
        fx: parseFloat(newLoad.fx) || 0,
        fy: parseFloat(newLoad.fy) || 0,
      }
      const updatedLoads = [...loads.filter(l => l.node_id !== load.node_id), load]
      setLoads(updatedLoads)
      setNewLoad({ nodeId: '', fx: '', fy: '' })
    }
  }

  const handleReanalyze = () => {
    reanalyzeMutation.mutate({ material: selectedMaterial, loads })
  }

  const handleExport = () => {
    if (analysis) {
      const dataStr = JSON.stringify(analysis, null, 2)
      const blob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `analysis-${id}.json`
      link.click()
      URL.revokeObjectURL(url)
    }
  }

  const handleDownloadPDF = async () => {
    if (!id) return
    
    try {
      const response = await fetch(`http://localhost:8000/api/v1/analysis/${id}/report`)
      if (!response.ok) {
        throw new Error('Failed to generate PDF report')
      }
      
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `analysis-report-${id.slice(0, 8)}.pdf`
      link.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error downloading PDF:', error)
      alert('Failed to generate PDF report. Please try again.')
    }
  }

  const handleCaptureImage = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    
    canvas.toBlob((blob) => {
      if (blob) {
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `analysis-${id}.png`
        link.click()
        URL.revokeObjectURL(url)
      }
    })
  }

  const handleModelEdit = (model: StructuralModel) => {
    // Convert model to API format and reanalyze
    const apiLoads = model.nodes
      .filter(n => n.loads && (n.loads.fx !== 0 || n.loads.fy !== 0))
      .map(n => ({
        node_id: parseInt(n.id),
        fx: n.loads!.fx,
        fy: n.loads!.fy,
      }))

    reanalyzeMutation.mutate({
      material: model.members[0]?.material || 'steel',
      loads: apiLoads.length > 0 ? apiLoads : undefined,
    })
    
    setShowEditor(false)
  }

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-xl text-gray-600">⏳ Loading analysis...</div>
        </div>
      </div>
    )
  }

  if (error || !analysis) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Failed to load analysis. Please try again.
        </div>
        <Link to="/history" className="text-blue-600 hover:underline mt-4 inline-block">
          ← Back to History
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <Link to="/history" className="text-blue-600 hover:underline text-sm mb-2 inline-block">
            ← Back to History
          </Link>
          <h1 className="text-3xl font-bold">Analysis Results</h1>
          <p className="text-gray-600 mt-1">
            {analysis.structure_type} • {analysis.member_count} members • {analysis.node_count} nodes
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowEditor(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            ✏️ Edit Model
          </button>
          <button
            onClick={handleDownloadPDF}
            className="bg-red-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-red-700 transition"
          >
            📄 Download PDF
          </button>
          <button
            onClick={handleCaptureImage}
            className="bg-green-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-green-700 transition"
          >
            📸 Save Image
          </button>
          <button
            onClick={handleExport}
            className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg font-semibold hover:bg-gray-300 transition"
          >
            📥 Export JSON
          </button>
        </div>
      </div>

      {/* Visualization */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Structure Visualization</h2>
          <div className="flex gap-4 text-sm">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showDeformed}
                onChange={(e) => setShowDeformed(e.target.checked)}
                className="rounded"
              />
              <span>Show Deformed</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showStress}
                onChange={(e) => setShowStress(e.target.checked)}
                className="rounded"
              />
              <span>Color by Stress</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showForces}
                onChange={(e) => setShowForces(e.target.checked)}
                className="rounded"
              />
              <span>Show Forces</span>
            </label>
          </div>
        </div>
        
        {showDeformed && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Deformation Scale: {deformationScale}x
            </label>
            <input
              type="range"
              min="10"
              max="200"
              value={deformationScale}
              onChange={(e) => setDeformationScale(Number(e.target.value))}
              className="w-full"
            />
          </div>
        )}
        
        <ResultsVisualization
          nodes={analysis.nodes}
          members={analysis.members}
          loads={analysis.loads}
          showDeformed={showDeformed}
          showStress={showStress}
          showForces={showForces}
          deformationScale={deformationScale}
        />
      </div>

      {/* What-If Controls */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">What-If Analysis</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Material
            </label>
            <select
              value={selectedMaterial}
              onChange={(e) => handleMaterialChange(e.target.value)}
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="steel">Steel</option>
              <option value="aluminum">Aluminum</option>
              <option value="wood">Wood</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Add/Modify Point Load
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                placeholder="Node ID"
                value={newLoad.nodeId}
                onChange={(e) => setNewLoad({ ...newLoad, nodeId: e.target.value })}
                className="w-24 px-2 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="number"
                step="0.1"
                placeholder="Fx (kips)"
                value={newLoad.fx}
                onChange={(e) => setNewLoad({ ...newLoad, fx: e.target.value })}
                className="flex-1 px-2 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="number"
                step="0.1"
                placeholder="Fy (kips)"
                value={newLoad.fy}
                onChange={(e) => setNewLoad({ ...newLoad, fy: e.target.value })}
                className="flex-1 px-2 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleAddLoad}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
              >
                Add
              </button>
            </div>
          </div>
        </div>

        {loads.length > 0 && (
          <div className="mt-4">
            <p className="text-sm font-semibold text-gray-700 mb-2">Current Loads:</p>
            <div className="flex flex-wrap gap-2">
              {loads.map((load, idx) => (
                <span key={idx} className="bg-blue-50 text-blue-700 px-3 py-1 rounded text-sm">
                  Node {load.node_id}: Fx={load.fx}, Fy={load.fy}
                </span>
              ))}
            </div>
          </div>
        )}

        <button
          onClick={handleReanalyze}
          disabled={reanalyzeMutation.isPending}
          className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 transition disabled:bg-gray-400"
        >
          {reanalyzeMutation.isPending ? '⏳ Reanalyzing...' : '🔄 Reanalyze'}
        </button>
      </div>

      {/* Results Panel */}
      <div className="grid md:grid-cols-2 gap-6 mb-6">
        {/* Member Forces */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Member Forces</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left">Member</th>
                  <th className="px-3 py-2 text-right">Force (kips)</th>
                  <th className="px-3 py-2 text-left">Status</th>
                </tr>
              </thead>
              <tbody>
                {analysis.members.map((member) => (
                  <tr key={member.id} className="border-t">
                    <td className="px-3 py-2">{member.id}</td>
                    <td className="px-3 py-2 text-right font-mono">
                      {member.axial_force.toFixed(2)}
                    </td>
                    <td className="px-3 py-2">
                      {Math.abs(member.axial_force) < 0.01 ? (
                        <span className="text-gray-600">Zero</span>
                      ) : member.axial_force > 0 ? (
                        <span className="text-red-600 font-semibold">Tension</span>
                      ) : (
                        <span className="text-blue-600 font-semibold">Compression</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Reactions */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Reactions</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left">Node</th>
                  <th className="px-3 py-2 text-right">Rx (kips)</th>
                  <th className="px-3 py-2 text-right">Ry (kips)</th>
                </tr>
              </thead>
              <tbody>
                {analysis.nodes
                  .filter(node => node.reaction_x || node.reaction_y)
                  .map((node) => (
                    <tr key={node.id} className="border-t">
                      <td className="px-3 py-2">{node.id}</td>
                      <td className="px-3 py-2 text-right font-mono">
                        {node.reaction_x?.toFixed(2) || '0.00'}
                      </td>
                      <td className="px-3 py-2 text-right font-mono">
                        {node.reaction_y?.toFixed(2) || '0.00'}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Safety Summary */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Safety Summary</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-3xl font-bold text-gray-900">
              {analysis.max_deflection.toFixed(3)}"
            </div>
            <div className="text-sm text-gray-600 mt-1">Max Deflection</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-3xl font-bold text-gray-900">
              {Math.max(...analysis.members.map(m => m.stress_ratio)).toFixed(2)}
            </div>
            <div className="text-sm text-gray-600 mt-1">Max Stress Ratio</div>
          </div>
          <div className="text-center p-4 rounded" 
               style={{ backgroundColor: analysis.safety_status === 'pass' ? '#D1FAE5' : '#FEE2E2' }}>
            <div className={`text-3xl font-bold ${analysis.safety_status === 'pass' ? 'text-green-700' : 'text-red-700'}`}>
              {analysis.safety_status === 'pass' ? '✓ PASS' : '✗ FAIL'}
            </div>
            <div className={`text-sm mt-1 ${analysis.safety_status === 'pass' ? 'text-green-600' : 'text-red-600'}`}>
              Safety Status
            </div>
          </div>
        </div>
      </div>

      {/* Model Editor Modal */}
      {showEditor && editableModel && (
        <div className="fixed inset-0 z-50 bg-white">
          <div className="absolute top-4 right-4 z-10">
            <button
              onClick={() => setShowEditor(false)}
              className="bg-white border shadow-lg px-4 py-2 rounded-lg font-semibold hover:bg-gray-100 transition"
            >
              ✕ Close Editor
            </button>
          </div>
          <ModelEditor
            initialModel={editableModel}
            backgroundImage={analysis.image_url}
            onAnalyze={handleModelEdit}
          />
        </div>
      )}
    </div>
  )
}

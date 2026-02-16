import { useReducer, useRef, useEffect, useCallback } from 'react'
import {
  EditorState,
  EditorAction,
  StructuralModel,
  Node,
  Member,
  EditorMode,
  ViewportTransform,
} from '../types/model'
import EditorToolbar from './EditorToolbar'
import PropertiesPanel from './PropertiesPanel'

interface ModelEditorProps {
  initialModel: StructuralModel
  backgroundImage?: string
  onAnalyze: (model: StructuralModel) => void
}

// Initial state
const createInitialState = (model: StructuralModel): EditorState => ({
  model,
  selection: { type: null, id: null },
  mode: 'select',
  tempMemberStart: null,
  viewport: { scale: 1, offsetX: 0, offsetY: 0 },
  history: [model],
  historyIndex: 0,
})

// Reducer for state management
function editorReducer(state: EditorState, action: EditorAction): EditorState {
  switch (action.type) {
    case 'SET_MODE':
      return { ...state, mode: action.mode, tempMemberStart: null }

    case 'SET_MODEL':
      return { ...state, model: action.model }

    case 'ADD_NODE': {
      const newModel = {
        ...state.model,
        nodes: [...state.model.nodes, action.node],
      }
      return saveToHistory({ ...state, model: newModel })
    }

    case 'UPDATE_NODE': {
      const newModel = {
        ...state.model,
        nodes: state.model.nodes.map((n) =>
          n.id === action.id ? { ...n, ...action.updates } : n
        ),
      }
      return saveToHistory({ ...state, model: newModel })
    }

    case 'DELETE_NODE': {
      const newModel = {
        nodes: state.model.nodes.filter((n) => n.id !== action.id),
        members: state.model.members.filter(
          (m) => m.startNodeId !== action.id && m.endNodeId !== action.id
        ),
      }
      return saveToHistory({
        ...state,
        model: newModel,
        selection: { type: null, id: null },
      })
    }

    case 'ADD_MEMBER': {
      const newModel = {
        ...state.model,
        members: [...state.model.members, action.member],
      }
      return saveToHistory({ ...state, model: newModel, tempMemberStart: null })
    }

    case 'UPDATE_MEMBER': {
      const newModel = {
        ...state.model,
        members: state.model.members.map((m) =>
          m.id === action.id ? { ...m, ...action.updates } : m
        ),
      }
      return saveToHistory({ ...state, model: newModel })
    }

    case 'DELETE_MEMBER': {
      const newModel = {
        ...state.model,
        members: state.model.members.filter((m) => m.id !== action.id),
      }
      return saveToHistory({
        ...state,
        model: newModel,
        selection: { type: null, id: null },
      })
    }

    case 'SELECT':
      return { ...state, selection: action.selection }

    case 'SET_TEMP_MEMBER_START':
      return { ...state, tempMemberStart: action.nodeId }

    case 'SET_VIEWPORT':
      return { ...state, viewport: action.viewport }

    case 'ZOOM_IN':
      return {
        ...state,
        viewport: { ...state.viewport, scale: state.viewport.scale * 1.2 },
      }

    case 'ZOOM_OUT':
      return {
        ...state,
        viewport: { ...state.viewport, scale: state.viewport.scale / 1.2 },
      }

    case 'FIT_TO_VIEW': {
      if (state.model.nodes.length === 0) return state
      
      const xs = state.model.nodes.map((n) => n.x)
      const ys = state.model.nodes.map((n) => n.y)
      const minX = Math.min(...xs)
      const maxX = Math.max(...xs)
      const minY = Math.min(...ys)
      const maxY = Math.max(...ys)
      
      const rangeX = maxX - minX || 100
      const rangeY = maxY - minY || 100
      
      const padding = 80
      const scaleX = (action.canvasWidth - 2 * padding) / rangeX
      const scaleY = (action.canvasHeight - 2 * padding) / rangeY
      const scale = Math.min(scaleX, scaleY, 2) // Cap at 2x zoom
      
      const centerX = (minX + maxX) / 2
      const centerY = (minY + maxY) / 2
      
      return {
        ...state,
        viewport: {
          scale,
          offsetX: action.canvasWidth / 2 - centerX * scale,
          offsetY: action.canvasHeight / 2 - centerY * scale,
        },
      }
    }

    case 'UNDO': {
      if (state.historyIndex > 0) {
        const newIndex = state.historyIndex - 1
        return {
          ...state,
          model: state.history[newIndex],
          historyIndex: newIndex,
          selection: { type: null, id: null },
        }
      }
      return state
    }

    case 'REDO': {
      if (state.historyIndex < state.history.length - 1) {
        const newIndex = state.historyIndex + 1
        return {
          ...state,
          model: state.history[newIndex],
          historyIndex: newIndex,
          selection: { type: null, id: null },
        }
      }
      return state
    }

    default:
      return state
  }
}

// Helper to save model to history
function saveToHistory(state: EditorState): EditorState {
  const newHistory = state.history.slice(0, state.historyIndex + 1)
  newHistory.push(state.model)
  
  // Limit history to 50 states
  const limitedHistory = newHistory.slice(-50)
  
  return {
    ...state,
    history: limitedHistory,
    historyIndex: limitedHistory.length - 1,
  }
}

export default function ModelEditor({
  initialModel,
  backgroundImage,
  onAnalyze,
}: ModelEditorProps) {
  const [state, dispatch] = useReducer(editorReducer, createInitialState(initialModel))
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const isPanningRef = useRef(false)
  const lastPanPointRef = useRef({ x: 0, y: 0 })
  const isDraggingNodeRef = useRef<string | null>(null)
  const backgroundImageRef = useRef<HTMLImageElement | null>(null)

  // Load background image
  useEffect(() => {
    if (backgroundImage) {
      const img = new Image()
      img.src = backgroundImage
      img.onload = () => {
        backgroundImageRef.current = img
        draw()
      }
    }
  }, [backgroundImage])

  // Transform canvas coordinates to model coordinates
  const canvasToModel = useCallback(
    (canvasX: number, canvasY: number): { x: number; y: number } => {
      return {
        x: (canvasX - state.viewport.offsetX) / state.viewport.scale,
        y: (canvasY - state.viewport.offsetY) / state.viewport.scale,
      }
    },
    [state.viewport]
  )

  // Transform model coordinates to canvas coordinates
  const modelToCanvas = useCallback(
    (modelX: number, modelY: number): { x: number; y: number } => {
      return {
        x: modelX * state.viewport.scale + state.viewport.offsetX,
        y: modelY * state.viewport.scale + state.viewport.offsetY,
      }
    },
    [state.viewport]
  )

  // Drawing function
  const draw = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Draw background image if available
    if (backgroundImageRef.current) {
      ctx.save()
      ctx.globalAlpha = 0.3
      ctx.drawImage(
        backgroundImageRef.current,
        state.viewport.offsetX,
        state.viewport.offsetY,
        backgroundImageRef.current.width * state.viewport.scale,
        backgroundImageRef.current.height * state.viewport.scale
      )
      ctx.restore()
    }

    // Draw grid (optional, light)
    drawGrid(ctx, canvas.width, canvas.height)

    // Draw members
    state.model.members.forEach((member) => {
      const startNode = state.model.nodes.find((n) => n.id === member.startNodeId)
      const endNode = state.model.nodes.find((n) => n.id === member.endNodeId)
      if (startNode && endNode) {
        const start = modelToCanvas(startNode.x, startNode.y)
        const end = modelToCanvas(endNode.x, endNode.y)
        const isSelected = state.selection.type === 'member' && state.selection.id === member.id
        drawMember(ctx, start, end, isSelected)
      }
    })

    // Draw temporary member line (during creation)
    if (state.tempMemberStart) {
      const startNode = state.model.nodes.find((n) => n.id === state.tempMemberStart)
      if (startNode) {
        const start = modelToCanvas(startNode.x, startNode.y)
        // Would need mouse position to draw to cursor - skip for now
      }
    }

    // Draw nodes and supports
    state.model.nodes.forEach((node) => {
      const pos = modelToCanvas(node.x, node.y)
      const isSelected = state.selection.type === 'node' && state.selection.id === node.id
      
      // Draw support
      if (node.support && node.support !== 'none') {
        drawSupport(ctx, pos.x, pos.y, node.support)
      }
      
      // Draw loads
      if (node.loads && (node.loads.fx !== 0 || node.loads.fy !== 0)) {
        drawLoad(ctx, pos.x, pos.y, node.loads.fx, node.loads.fy)
      }
      
      // Draw node
      drawNode(ctx, pos.x, pos.y, node.id, isSelected)
    })
  }, [state, modelToCanvas])

  // Draw grid
  const drawGrid = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
    const gridSize = 50 * state.viewport.scale
    if (gridSize < 10) return // Don't draw if too small

    ctx.strokeStyle = '#e5e7eb'
    ctx.lineWidth = 1

    // Vertical lines
    for (let x = state.viewport.offsetX % gridSize; x < width; x += gridSize) {
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, height)
      ctx.stroke()
    }

    // Horizontal lines
    for (let y = state.viewport.offsetY % gridSize; y < height; y += gridSize) {
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(width, y)
      ctx.stroke()
    }
  }

  // Draw member
  const drawMember = (
    ctx: CanvasRenderingContext2D,
    start: { x: number; y: number },
    end: { x: number; y: number },
    isSelected: boolean
  ) => {
    ctx.strokeStyle = isSelected ? '#3B82F6' : '#6B7280'
    ctx.lineWidth = isSelected ? 4 : 3
    ctx.beginPath()
    ctx.moveTo(start.x, start.y)
    ctx.lineTo(end.x, end.y)
    ctx.stroke()
  }

  // Draw node
  const drawNode = (
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    id: string,
    isSelected: boolean
  ) => {
    // Node circle
    ctx.fillStyle = isSelected ? '#3B82F6' : '#1F2937'
    ctx.beginPath()
    ctx.arc(x, y, 8, 0, Math.PI * 2)
    ctx.fill()

    // Selection ring
    if (isSelected) {
      ctx.strokeStyle = '#3B82F6'
      ctx.lineWidth = 3
      ctx.beginPath()
      ctx.arc(x, y, 12, 0, Math.PI * 2)
      ctx.stroke()
    }

    // Label
    ctx.fillStyle = '#1F2937'
    ctx.font = 'bold 12px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(id, x, y - 15)
  }

  // Draw support
  const drawSupport = (
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    type: 'pin' | 'roller' | 'fixed'
  ) => {
    ctx.fillStyle = '#059669'
    ctx.strokeStyle = '#059669'
    ctx.lineWidth = 2

    if (type === 'pin') {
      // Triangle
      ctx.beginPath()
      ctx.moveTo(x, y)
      ctx.lineTo(x - 12, y + 20)
      ctx.lineTo(x + 12, y + 20)
      ctx.closePath()
      ctx.fill()
    } else if (type === 'roller') {
      // Triangle + circles
      ctx.beginPath()
      ctx.moveTo(x, y)
      ctx.lineTo(x - 12, y + 20)
      ctx.lineTo(x + 12, y + 20)
      ctx.closePath()
      ctx.fill()
      
      ctx.beginPath()
      ctx.arc(x - 8, y + 25, 4, 0, Math.PI * 2)
      ctx.fill()
      ctx.beginPath()
      ctx.arc(x + 8, y + 25, 4, 0, Math.PI * 2)
      ctx.fill()
    } else if (type === 'fixed') {
      // Rectangle
      ctx.fillRect(x - 15, y, 30, 20)
      // Hatching
      ctx.strokeStyle = '#ffffff'
      for (let i = 0; i < 6; i++) {
        ctx.beginPath()
        ctx.moveTo(x - 15 + i * 6, y + 20)
        ctx.lineTo(x - 15 + i * 6 + 6, y)
        ctx.stroke()
      }
    }
  }

  // Draw load arrow
  const drawLoad = (
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    fx: number,
    fy: number
  ) => {
    const arrowScale = 30
    ctx.strokeStyle = '#F59E0B'
    ctx.fillStyle = '#F59E0B'
    ctx.lineWidth = 3

    if (Math.abs(fx) > 0.01) {
      drawArrow(ctx, x, y, x + fx * arrowScale, y)
    }
    if (Math.abs(fy) > 0.01) {
      drawArrow(ctx, x, y, x, y - fy * arrowScale)
    }
  }

  // Draw arrow
  const drawArrow = (
    ctx: CanvasRenderingContext2D,
    x1: number,
    y1: number,
    x2: number,
    y2: number
  ) => {
    const headlen = 10
    const dx = x2 - x1
    const dy = y2 - y1
    const angle = Math.atan2(dy, dx)

    // Line
    ctx.beginPath()
    ctx.moveTo(x1, y1)
    ctx.lineTo(x2, y2)
    ctx.stroke()

    // Arrowhead
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

  // Redraw when state changes
  useEffect(() => {
    draw()
  }, [draw])

  // Handle canvas resize
  useEffect(() => {
    const resizeCanvas = () => {
      const canvas = canvasRef.current
      const container = containerRef.current
      if (canvas && container) {
        canvas.width = container.clientWidth
        canvas.height = container.clientHeight
        draw()
      }
    }

    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)
    return () => window.removeEventListener('resize', resizeCanvas)
  }, [draw])

  // Get node at position
  const getNodeAt = (canvasX: number, canvasY: number): Node | null => {
    const hitRadius = 12
    for (const node of state.model.nodes) {
      const pos = modelToCanvas(node.x, node.y)
      const dx = canvasX - pos.x
      const dy = canvasY - pos.y
      if (Math.sqrt(dx * dx + dy * dy) <= hitRadius) {
        return node
      }
    }
    return null
  }

  // Get member at position
  const getMemberAt = (canvasX: number, canvasY: number): Member | null => {
    const hitRadius = 8
    for (const member of state.model.members) {
      const startNode = state.model.nodes.find((n) => n.id === member.startNodeId)
      const endNode = state.model.nodes.find((n) => n.id === member.endNodeId)
      if (startNode && endNode) {
        const start = modelToCanvas(startNode.x, startNode.y)
        const end = modelToCanvas(endNode.x, endNode.y)
        
        // Distance from point to line segment
        const dist = distanceToSegment(canvasX, canvasY, start.x, start.y, end.x, end.y)
        if (dist <= hitRadius) {
          return member
        }
      }
    }
    return null
  }

  // Distance from point to line segment
  const distanceToSegment = (
    px: number,
    py: number,
    x1: number,
    y1: number,
    x2: number,
    y2: number
  ): number => {
    const dx = x2 - x1
    const dy = y2 - y1
    const lengthSq = dx * dx + dy * dy
    
    if (lengthSq === 0) return Math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
    
    let t = ((px - x1) * dx + (py - y1) * dy) / lengthSq
    t = Math.max(0, Math.min(1, t))
    
    const nearestX = x1 + t * dx
    const nearestY = y1 + t * dy
    
    return Math.sqrt((px - nearestX) ** 2 + (py - nearestY) ** 2)
  }

  // Mouse down handler
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const canvasX = e.clientX - rect.left
    const canvasY = e.clientY - rect.top

    // Check for node hit
    const hitNode = getNodeAt(canvasX, canvasY)

    if (state.mode === 'select') {
      if (hitNode) {
        dispatch({ type: 'SELECT', selection: { type: 'node', id: hitNode.id } })
        isDraggingNodeRef.current = hitNode.id
      } else {
        const hitMember = getMemberAt(canvasX, canvasY)
        if (hitMember) {
          dispatch({ type: 'SELECT', selection: { type: 'member', id: hitMember.id } })
        } else {
          dispatch({ type: 'SELECT', selection: { type: null, id: null } })
          isPanningRef.current = true
          lastPanPointRef.current = { x: canvasX, y: canvasY }
        }
      }
    } else if (state.mode === 'add-node') {
      if (!hitNode) {
        const modelPos = canvasToModel(canvasX, canvasY)
        const newNode: Node = {
          id: `N${state.model.nodes.length + 1}`,
          x: Math.round(modelPos.x),
          y: Math.round(modelPos.y),
          support: 'none',
        }
        dispatch({ type: 'ADD_NODE', node: newNode })
      }
    } else if (state.mode === 'add-member') {
      if (hitNode) {
        if (!state.tempMemberStart) {
          dispatch({ type: 'SET_TEMP_MEMBER_START', nodeId: hitNode.id })
        } else if (state.tempMemberStart !== hitNode.id) {
          const newMember: Member = {
            id: `M${state.model.members.length + 1}`,
            startNodeId: state.tempMemberStart,
            endNodeId: hitNode.id,
            material: 'steel',
          }
          dispatch({ type: 'ADD_MEMBER', member: newMember })
        }
      }
    } else if (state.mode === 'delete') {
      if (hitNode) {
        if (window.confirm(`Delete node ${hitNode.id}?`)) {
          dispatch({ type: 'DELETE_NODE', id: hitNode.id })
        }
      } else {
        const hitMember = getMemberAt(canvasX, canvasY)
        if (hitMember && window.confirm(`Delete member ${hitMember.id}?`)) {
          dispatch({ type: 'DELETE_MEMBER', id: hitMember.id })
        }
      }
    }
  }

  // Mouse move handler
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const canvasX = e.clientX - rect.left
    const canvasY = e.clientY - rect.top

    if (isPanningRef.current) {
      const dx = canvasX - lastPanPointRef.current.x
      const dy = canvasY - lastPanPointRef.current.y
      dispatch({
        type: 'SET_VIEWPORT',
        viewport: {
          ...state.viewport,
          offsetX: state.viewport.offsetX + dx,
          offsetY: state.viewport.offsetY + dy,
        },
      })
      lastPanPointRef.current = { x: canvasX, y: canvasY }
    } else if (isDraggingNodeRef.current) {
      const modelPos = canvasToModel(canvasX, canvasY)
      dispatch({
        type: 'UPDATE_NODE',
        id: isDraggingNodeRef.current,
        updates: { x: Math.round(modelPos.x), y: Math.round(modelPos.y) },
      })
    }
  }

  // Mouse up handler
  const handleMouseUp = () => {
    isPanningRef.current = false
    isDraggingNodeRef.current = null
  }

  // Wheel handler for zoom
  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault()
    
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top

    const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1
    const newScale = state.viewport.scale * zoomFactor

    // Zoom towards mouse position
    const newOffsetX = mouseX - (mouseX - state.viewport.offsetX) * zoomFactor
    const newOffsetY = mouseY - (mouseY - state.viewport.offsetY) * zoomFactor

    dispatch({
      type: 'SET_VIEWPORT',
      viewport: {
        scale: newScale,
        offsetX: newOffsetX,
        offsetY: newOffsetY,
      },
    })
  }

  // Keyboard handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        if (e.key === 'z' && !e.shiftKey) {
          e.preventDefault()
          dispatch({ type: 'UNDO' })
        } else if (e.key === 'z' && e.shiftKey) {
          e.preventDefault()
          dispatch({ type: 'REDO' })
        }
      } else if (e.key === 'Delete' || e.key === 'Backspace') {
        if (state.selection.type === 'node' && state.selection.id) {
          if (window.confirm(`Delete node ${state.selection.id}?`)) {
            dispatch({ type: 'DELETE_NODE', id: state.selection.id })
          }
        } else if (state.selection.type === 'member' && state.selection.id) {
          if (window.confirm(`Delete member ${state.selection.id}?`)) {
            dispatch({ type: 'DELETE_MEMBER', id: state.selection.id })
          }
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [state.selection])

  // Get selected node/member for properties panel
  const selectedNode = state.selection.type === 'node' && state.selection.id
    ? state.model.nodes.find((n) => n.id === state.selection.id) || null
    : null

  const selectedMember = state.selection.type === 'member' && state.selection.id
    ? state.model.members.find((m) => m.id === state.selection.id) || null
    : null

  return (
    <div className="flex flex-col h-screen">
      <EditorToolbar
        mode={state.mode}
        onModeChange={(mode: EditorMode) => dispatch({ type: 'SET_MODE', mode })}
        canUndo={state.historyIndex > 0}
        canRedo={state.historyIndex < state.history.length - 1}
        onUndo={() => dispatch({ type: 'UNDO' })}
        onRedo={() => dispatch({ type: 'REDO' })}
        onZoomIn={() => dispatch({ type: 'ZOOM_IN' })}
        onZoomOut={() => dispatch({ type: 'ZOOM_OUT' })}
        onFitToView={() => {
          const canvas = canvasRef.current
          if (canvas) {
            dispatch({
              type: 'FIT_TO_VIEW',
              canvasWidth: canvas.width,
              canvasHeight: canvas.height,
            })
          }
        }}
        onAnalyze={() => onAnalyze(state.model)}
      />

      <div className="flex flex-1 overflow-hidden">
        <div ref={containerRef} className="flex-1 bg-gray-100">
          <canvas
            ref={canvasRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onWheel={handleWheel}
            className="cursor-crosshair"
          />
        </div>

        <PropertiesPanel
          model={state.model}
          selectedNode={selectedNode}
          selectedMember={selectedMember}
          onUpdateNode={(id, updates) => dispatch({ type: 'UPDATE_NODE', id, updates })}
          onUpdateMember={(id, updates) => dispatch({ type: 'UPDATE_MEMBER', id, updates })}
        />
      </div>
    </div>
  )
}

import { useRef, useEffect, useCallback } from 'react'

interface Node {
  id: number
  x: number
  y: number
  support_type?: string | null
  reaction_x?: number
  reaction_y?: number
  displacement_x?: number
  displacement_y?: number
}

interface Member {
  id: number
  start_node: number
  end_node: number
  axial_force: number
  stress?: number
  stress_ratio: number
}

interface Load {
  node_id: number
  fx: number
  fy: number
}

interface ResultsVisualizationProps {
  nodes: Node[]
  members: Member[]
  loads: Load[]
  showDeformed?: boolean
  showStress?: boolean
  showForces?: boolean
  deformationScale?: number
}

export default function ResultsVisualization({
  nodes,
  members,
  loads,
  showDeformed = false,
  showStress = true,
  showForces = true,
  deformationScale = 50,
}: ResultsVisualizationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const getStressColor = useCallback((stressRatio: number): string => {
    if (stressRatio >= 1.0) return '#EF4444' // Red - failure
    if (stressRatio >= 0.8) return '#F59E0B' // Yellow/Orange - warning
    return '#10B981' // Green - safe
  }, [])

  const draw = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size
    const containerWidth = canvas.parentElement?.clientWidth || 800
    canvas.width = containerWidth
    canvas.height = 600

    ctx.clearRect(0, 0, canvas.width, canvas.height)

    if (nodes.length === 0) return

    // Calculate bounds
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

    // Transform function (from model to canvas coords)
    const transform = (x: number, y: number): [number, number] => {
      const tx = padding + (x - minX) * scale
      const ty = canvas.height - (padding + (y - minY) * scale) // Flip Y axis
      return [tx, ty]
    }

    // Draw original structure in light gray if showing deformed
    if (showDeformed) {
      members.forEach(member => {
        const startNode = nodes.find(n => n.id === member.start_node)
        const endNode = nodes.find(n => n.id === member.end_node)
        
        if (startNode && endNode) {
          const [x1, y1] = transform(startNode.x, startNode.y)
          const [x2, y2] = transform(endNode.x, endNode.y)

          ctx.strokeStyle = '#D1D5DB'
          ctx.lineWidth = 1
          ctx.setLineDash([5, 5])
          ctx.beginPath()
          ctx.moveTo(x1, y1)
          ctx.lineTo(x2, y2)
          ctx.stroke()
          ctx.setLineDash([])
        }
      })
    }

    // Draw members with stress coloring or force indication
    members.forEach(member => {
      const startNode = nodes.find(n => n.id === member.start_node)
      const endNode = nodes.find(n => n.id === member.end_node)
      
      if (startNode && endNode) {
        // Calculate deformed positions
        let x1 = startNode.x
        let y1 = startNode.y
        let x2 = endNode.x
        let y2 = endNode.y

        if (showDeformed && startNode.displacement_x !== undefined) {
          x1 += (startNode.displacement_x || 0) * deformationScale
          y1 += (startNode.displacement_y || 0) * deformationScale
          x2 += (endNode.displacement_x || 0) * deformationScale
          y2 += (endNode.displacement_y || 0) * deformationScale
        }

        const [cx1, cy1] = transform(x1, y1)
        const [cx2, cy2] = transform(x2, y2)

        // Determine color
        let color = '#6B7280' // gray for default
        if (showStress) {
          color = getStressColor(member.stress_ratio)
        } else if (showForces && Math.abs(member.axial_force) > 0.01) {
          color = member.axial_force > 0 ? '#EF4444' : '#3B82F6' // red for tension, blue for compression
        }

        // Line thickness
        const maxForce = Math.max(...members.map(m => Math.abs(m.axial_force)), 1)
        const lineWidth = showForces 
          ? Math.max(2, Math.min(10, (Math.abs(member.axial_force) / maxForce) * 8 + 2))
          : 3

        ctx.strokeStyle = color
        ctx.lineWidth = lineWidth
        ctx.beginPath()
        ctx.moveTo(cx1, cy1)
        ctx.lineTo(cx2, cy2)
        ctx.stroke()

        // Draw force arrow indicator if showing forces
        if (showForces && Math.abs(member.axial_force) > 0.01) {
          const midX = (cx1 + cx2) / 2
          const midY = (cy1 + cy2) / 2
          
          // Draw force label
          ctx.fillStyle = color
          ctx.font = 'bold 11px sans-serif'
          ctx.textAlign = 'center'
          ctx.fillText(`${member.axial_force.toFixed(1)}k`, midX, midY - 5)

          // Draw direction arrow
          const angle = Math.atan2(cy2 - cy1, cx2 - cx1)
          const arrowSize = 8
          
          if (member.axial_force > 0) {
            // Tension - arrows pointing outward
            drawArrowHead(ctx, cx1, cy1, angle + Math.PI, arrowSize, color)
            drawArrowHead(ctx, cx2, cy2, angle, arrowSize, color)
          } else {
            // Compression - arrows pointing inward
            drawArrowHead(ctx, cx1, cy1, angle, arrowSize, color)
            drawArrowHead(ctx, cx2, cy2, angle + Math.PI, arrowSize, color)
          }
        }

        // Draw stress ratio if showing stress
        if (showStress && member.stress_ratio > 0.01) {
          const midX = (cx1 + cx2) / 2
          const midY = (cy1 + cy2) / 2
          
          ctx.fillStyle = color
          ctx.font = 'bold 10px sans-serif'
          ctx.textAlign = 'center'
          ctx.fillText(`${(member.stress_ratio * 100).toFixed(0)}%`, midX, midY + 15)
        }
      }
    })

    // Draw loads
    loads.forEach(load => {
      const node = nodes.find(n => n.id === load.node_id)
      if (node) {
        let x = node.x
        let y = node.y

        if (showDeformed && node.displacement_x !== undefined) {
          x += (node.displacement_x || 0) * deformationScale
          y += (node.displacement_y || 0) * deformationScale
        }

        const [cx, cy] = transform(x, y)
        
        // Draw load arrows
        const arrowScale = 30
        if (Math.abs(load.fx) > 0.01) {
          drawArrow(ctx, cx, cy, cx + load.fx * arrowScale, cy, '#F59E0B', 3)
        }
        if (Math.abs(load.fy) > 0.01) {
          drawArrow(ctx, cx, cy, cx, cy - load.fy * arrowScale, '#F59E0B', 3)
        }
      }
    })

    // Draw nodes and supports
    nodes.forEach(node => {
      let x = node.x
      let y = node.y

      if (showDeformed && node.displacement_x !== undefined) {
        x += (node.displacement_x || 0) * deformationScale
        y += (node.displacement_y || 0) * deformationScale
      }

      const [cx, cy] = transform(x, y)

      // Draw support symbols
      if (node.support_type === 'pin') {
        drawPinSupport(ctx, cx, cy)
      } else if (node.support_type === 'roller') {
        drawRollerSupport(ctx, cx, cy)
      } else if (node.support_type === 'fixed') {
        drawFixedSupport(ctx, cx, cy)
      }

      // Draw node circle
      ctx.fillStyle = '#1F2937'
      ctx.beginPath()
      ctx.arc(cx, cy, 6, 0, Math.PI * 2)
      ctx.fill()

      // Draw node label
      ctx.fillStyle = '#1F2937'
      ctx.font = 'bold 12px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(`${node.id}`, cx, cy - 12)

      // Draw reactions if present
      if (node.reaction_x || node.reaction_y) {
        ctx.fillStyle = '#059669'
        ctx.font = '10px sans-serif'
        const rxText = node.reaction_x ? `Rx:${node.reaction_x.toFixed(1)}` : ''
        const ryText = node.reaction_y ? `Ry:${node.reaction_y.toFixed(1)}` : ''
        ctx.fillText(`${rxText} ${ryText}`, cx, cy + 20)
      }
    })

    // Draw legend
    drawLegend(ctx, canvas.width - 180, 20, showStress, showForces)
  }, [nodes, members, loads, showDeformed, showStress, showForces, deformationScale, getStressColor])

  // Helper drawing functions
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

  const drawArrowHead = (
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    angle: number,
    size: number,
    color: string
  ) => {
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.moveTo(x, y)
    ctx.lineTo(
      x - size * Math.cos(angle - Math.PI / 6),
      y - size * Math.sin(angle - Math.PI / 6)
    )
    ctx.lineTo(
      x - size * Math.cos(angle + Math.PI / 6),
      y - size * Math.sin(angle + Math.PI / 6)
    )
    ctx.closePath()
    ctx.fill()
  }

  const drawPinSupport = (ctx: CanvasRenderingContext2D, x: number, y: number) => {
    ctx.fillStyle = '#059669'
    ctx.strokeStyle = '#059669'
    ctx.lineWidth = 2
    
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
  }

  const drawFixedSupport = (ctx: CanvasRenderingContext2D, x: number, y: number) => {
    ctx.fillStyle = '#059669'
    ctx.strokeStyle = '#059669'
    ctx.lineWidth = 2
    
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

  const drawLegend = (
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    showStress: boolean,
    showForces: boolean
  ) => {
    ctx.font = 'bold 12px sans-serif'
    ctx.fillStyle = '#1F2937'
    ctx.textAlign = 'left'
    ctx.fillText('Legend:', x, y)

    let offsetY = y + 15

    if (showStress) {
      // Safe (green)
      ctx.strokeStyle = '#10B981'
      ctx.lineWidth = 3
      ctx.beginPath()
      ctx.moveTo(x, offsetY)
      ctx.lineTo(x + 30, offsetY)
      ctx.stroke()
      ctx.fillStyle = '#1F2937'
      ctx.font = '11px sans-serif'
      ctx.fillText('Safe (<80%)', x + 35, offsetY + 3)
      offsetY += 15

      // Warning (yellow)
      ctx.strokeStyle = '#F59E0B'
      ctx.lineWidth = 3
      ctx.beginPath()
      ctx.moveTo(x, offsetY)
      ctx.lineTo(x + 30, offsetY)
      ctx.stroke()
      ctx.fillText('Warning (80-100%)', x + 35, offsetY + 3)
      offsetY += 15

      // Failure (red)
      ctx.strokeStyle = '#EF4444'
      ctx.lineWidth = 3
      ctx.beginPath()
      ctx.moveTo(x, offsetY)
      ctx.lineTo(x + 30, offsetY)
      ctx.stroke()
      ctx.fillText('Failure (>100%)', x + 35, offsetY + 3)
      offsetY += 15
    }

    if (showForces) {
      // Tension
      ctx.strokeStyle = '#EF4444'
      ctx.lineWidth = 3
      ctx.beginPath()
      ctx.moveTo(x, offsetY)
      ctx.lineTo(x + 30, offsetY)
      ctx.stroke()
      ctx.fillStyle = '#1F2937'
      ctx.font = '11px sans-serif'
      ctx.fillText('Tension', x + 35, offsetY + 3)
      offsetY += 15

      // Compression
      ctx.strokeStyle = '#3B82F6'
      ctx.lineWidth = 3
      ctx.beginPath()
      ctx.moveTo(x, offsetY)
      ctx.lineTo(x + 30, offsetY)
      ctx.stroke()
      ctx.fillText('Compression', x + 35, offsetY + 3)
    }
  }

  // Redraw when data changes
  useEffect(() => {
    draw()
  }, [draw])

  // Handle canvas resize
  useEffect(() => {
    const resizeCanvas = () => {
      draw()
    }

    window.addEventListener('resize', resizeCanvas)
    return () => window.removeEventListener('resize', resizeCanvas)
  }, [draw])

  return (
    <div className="border rounded-lg overflow-hidden bg-gray-50">
      <canvas ref={canvasRef} className="w-full" />
    </div>
  )
}

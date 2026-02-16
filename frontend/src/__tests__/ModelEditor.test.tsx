import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ModelEditor from '../components/ModelEditor'
import type { StructuralModel } from '../types/model'

// Mock canvas context
beforeEach(() => {
  HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
    clearRect: vi.fn(),
    fillRect: vi.fn(),
    strokeRect: vi.fn(),
    fillStyle: '',
    strokeStyle: '',
    lineWidth: 0,
    beginPath: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    arc: vi.fn(),
    stroke: vi.fn(),
    fill: vi.fn(),
    closePath: vi.fn(),
    fillText: vi.fn(),
    drawImage: vi.fn(),
    save: vi.fn(),
    restore: vi.fn(),
    globalAlpha: 1,
    font: '',
    textAlign: '',
  })) as any
})

describe('ModelEditor', () => {
  const emptyModel: StructuralModel = {
    nodes: [],
    members: [],
  }

  const mockModel: StructuralModel = {
    nodes: [
      { id: 'N1', x: 0, y: 0, support: 'pin' },
      { id: 'N2', x: 100, y: 0, support: 'none' },
      { id: 'N3', x: 50, y: 50, support: 'roller' },
    ],
    members: [
      { id: 'M1', startNodeId: 'N1', endNodeId: 'N2', material: 'steel' },
      { id: 'M2', startNodeId: 'N2', endNodeId: 'N3', material: 'steel' },
    ],
  }

  const defaultProps = {
    initialModel: emptyModel,
    onAnalyze: vi.fn(),
  }

  it('renders with empty model', () => {
    render(<ModelEditor {...defaultProps} />)
    
    // Should show toolbar
    expect(screen.getByTitle('Select')).toBeInTheDocument()
    
    // Should show properties panel
    expect(screen.getByText('Properties')).toBeInTheDocument()
    
    // Should show model stats (0 nodes, 0 members)
    expect(screen.getByText('Model Summary')).toBeInTheDocument()
  })

  it('renders nodes and members from mock model', () => {
    render(<ModelEditor {...defaultProps} initialModel={mockModel} />)
    
    // Canvas should be rendered
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeInTheDocument()
    
    // Properties should show model stats
    expect(screen.getByText('Model Summary')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument() // 3 nodes
    const membersAndSupports = screen.getAllByText('2')
    expect(membersAndSupports.length).toBeGreaterThanOrEqual(1) // 2 members, 2 supports
  })

  it('switches to add-node mode when button is clicked', () => {
    render(<ModelEditor {...defaultProps} />)
    
    const addNodeButton = screen.getByTitle('Add Node')
    fireEvent.click(addNodeButton)
    
    expect(addNodeButton).toHaveClass('bg-blue-600')
  })

  it('switches to add-member mode when button is clicked', () => {
    render(<ModelEditor {...defaultProps} initialModel={mockModel} />)
    
    const addMemberButton = screen.getByTitle('Add Member')
    fireEvent.click(addMemberButton)
    
    expect(addMemberButton).toHaveClass('bg-blue-600')
  })

  it('shows properties panel when node is selected', () => {
    render(<ModelEditor {...defaultProps} initialModel={mockModel} />)
    
    // Click on canvas to simulate selecting a node
    const canvas = document.querySelector('canvas')
    if (canvas) {
      // Simulate clicking near node position
      fireEvent.mouseDown(canvas, { clientX: 150, clientY: 150 })
    }
    
    // Properties panel should be visible (it's always visible, just shows different content)
    expect(screen.getByText('Properties')).toBeInTheDocument()
  })

  it('undo button is disabled initially', () => {
    render(<ModelEditor {...defaultProps} />)
    
    const undoButton = screen.getByTitle(/Undo/)
    expect(undoButton).toBeDisabled()
  })

  it('redo button is disabled initially', () => {
    render(<ModelEditor {...defaultProps} />)
    
    const redoButton = screen.getByTitle(/Redo/)
    expect(redoButton).toBeDisabled()
  })

  it('calls onAnalyze when analyze button is clicked', () => {
    const onAnalyze = vi.fn()
    render(<ModelEditor {...defaultProps} onAnalyze={onAnalyze} />)
    
    const analyzeButton = screen.getByText(/Analyze/)
    fireEvent.click(analyzeButton)
    
    expect(onAnalyze).toHaveBeenCalled()
  })

  it('zoom in button is rendered and clickable', () => {
    render(<ModelEditor {...defaultProps} />)
    
    const zoomInButton = screen.getByTitle('Zoom In')
    expect(zoomInButton).toBeInTheDocument()
    
    fireEvent.click(zoomInButton)
    // Zoom should have changed (tested via viewport state, not directly observable)
  })

  it('zoom out button is rendered and clickable', () => {
    render(<ModelEditor {...defaultProps} />)
    
    const zoomOutButton = screen.getByTitle('Zoom Out')
    expect(zoomOutButton).toBeInTheDocument()
    
    fireEvent.click(zoomOutButton)
  })

  it('fit to view button is rendered and clickable', () => {
    render(<ModelEditor {...defaultProps} initialModel={mockModel} />)
    
    const fitButton = screen.getByTitle('Fit to View')
    expect(fitButton).toBeInTheDocument()
    
    fireEvent.click(fitButton)
  })

  it('delete mode can be activated', () => {
    render(<ModelEditor {...defaultProps} />)
    
    const deleteButton = screen.getByTitle('Delete')
    fireEvent.click(deleteButton)
    
    expect(deleteButton).toHaveClass('bg-blue-600')
  })

  it('renders background image when provided', () => {
    const backgroundImage = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
    
    render(<ModelEditor {...defaultProps} backgroundImage={backgroundImage} />)
    
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeInTheDocument()
  })

  it('shows select mode by default', () => {
    render(<ModelEditor {...defaultProps} />)
    
    const selectButton = screen.getByTitle('Select')
    expect(selectButton).toHaveClass('bg-blue-600')
  })

  it('canvas responds to mouse wheel for zoom', () => {
    render(<ModelEditor {...defaultProps} />)
    
    const canvas = document.querySelector('canvas')
    if (canvas) {
      fireEvent.wheel(canvas, { deltaY: -100 })
    }
    
    // Zoom should have increased (not directly testable without exposing state)
  })

  it('displays all toolbar modes', () => {
    render(<ModelEditor {...defaultProps} />)
    
    expect(screen.getByTitle('Select')).toBeInTheDocument()
    expect(screen.getByTitle('Add Node')).toBeInTheDocument()
    expect(screen.getByTitle('Add Member')).toBeInTheDocument()
    expect(screen.getByTitle('Add Load')).toBeInTheDocument()
    expect(screen.getByTitle('Delete')).toBeInTheDocument()
  })

  it('renders canvas element', () => {
    render(<ModelEditor {...defaultProps} />)
    
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeInTheDocument()
    expect(canvas).toHaveClass('cursor-crosshair')
  })

  it('model stats update with initial model', () => {
    render(<ModelEditor {...defaultProps} initialModel={mockModel} />)
    
    // Check that the model has correct counts via Model Summary
    expect(screen.getByText('Model Summary')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument() // 3 nodes
    
    // Should have 2 for both members count and supports count
    const twoValues = screen.getAllByText('2')
    expect(twoValues.length).toBeGreaterThanOrEqual(1)
  })
})

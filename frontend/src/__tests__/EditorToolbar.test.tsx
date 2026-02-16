import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import EditorToolbar from '../components/EditorToolbar'

describe('EditorToolbar', () => {
  const defaultProps = {
    mode: 'select' as const,
    onModeChange: vi.fn(),
    canUndo: false,
    canRedo: false,
    onUndo: vi.fn(),
    onRedo: vi.fn(),
    onZoomIn: vi.fn(),
    onZoomOut: vi.fn(),
    onFitToView: vi.fn(),
    onAnalyze: vi.fn(),
  }

  it('renders all mode buttons', () => {
    render(<EditorToolbar {...defaultProps} />)
    
    expect(screen.getByTitle('Select')).toBeInTheDocument()
    expect(screen.getByTitle('Add Node')).toBeInTheDocument()
    expect(screen.getByTitle('Add Member')).toBeInTheDocument()
    expect(screen.getByTitle('Add Load')).toBeInTheDocument()
    expect(screen.getByTitle('Delete')).toBeInTheDocument()
  })

  it('highlights active mode button', () => {
    const { rerender } = render(<EditorToolbar {...defaultProps} mode="add-node" />)
    
    const addNodeButton = screen.getByTitle('Add Node')
    expect(addNodeButton).toHaveClass('bg-blue-600')
    
    rerender(<EditorToolbar {...defaultProps} mode="select" />)
    const selectButton = screen.getByTitle('Select')
    expect(selectButton).toHaveClass('bg-blue-600')
  })

  it('calls onModeChange when mode button is clicked', () => {
    const onModeChange = vi.fn()
    render(<EditorToolbar {...defaultProps} onModeChange={onModeChange} />)
    
    fireEvent.click(screen.getByTitle('Add Node'))
    expect(onModeChange).toHaveBeenCalledWith('add-node')
    
    fireEvent.click(screen.getByTitle('Delete'))
    expect(onModeChange).toHaveBeenCalledWith('delete')
  })

  it('renders undo/redo buttons', () => {
    render(<EditorToolbar {...defaultProps} />)
    
    expect(screen.getByTitle(/Undo/)).toBeInTheDocument()
    expect(screen.getByTitle(/Redo/)).toBeInTheDocument()
  })

  it('disables undo button when canUndo is false', () => {
    render(<EditorToolbar {...defaultProps} canUndo={false} />)
    
    const undoButton = screen.getByTitle(/Undo/)
    expect(undoButton).toBeDisabled()
  })

  it('enables undo button when canUndo is true', () => {
    render(<EditorToolbar {...defaultProps} canUndo={true} />)
    
    const undoButton = screen.getByTitle(/Undo/)
    expect(undoButton).not.toBeDisabled()
  })

  it('disables redo button when canRedo is false', () => {
    render(<EditorToolbar {...defaultProps} canRedo={false} />)
    
    const redoButton = screen.getByTitle(/Redo/)
    expect(redoButton).toBeDisabled()
  })

  it('calls onUndo when undo button is clicked', () => {
    const onUndo = vi.fn()
    render(<EditorToolbar {...defaultProps} canUndo={true} onUndo={onUndo} />)
    
    fireEvent.click(screen.getByTitle(/Undo/))
    expect(onUndo).toHaveBeenCalled()
  })

  it('calls onRedo when redo button is clicked', () => {
    const onRedo = vi.fn()
    render(<EditorToolbar {...defaultProps} canRedo={true} onRedo={onRedo} />)
    
    fireEvent.click(screen.getByTitle(/Redo/))
    expect(onRedo).toHaveBeenCalled()
  })

  it('renders zoom control buttons', () => {
    render(<EditorToolbar {...defaultProps} />)
    
    expect(screen.getByTitle('Zoom In')).toBeInTheDocument()
    expect(screen.getByTitle('Zoom Out')).toBeInTheDocument()
    expect(screen.getByTitle('Fit to View')).toBeInTheDocument()
  })

  it('calls zoom handlers when zoom buttons are clicked', () => {
    const onZoomIn = vi.fn()
    const onZoomOut = vi.fn()
    const onFitToView = vi.fn()
    
    render(<EditorToolbar {...defaultProps} onZoomIn={onZoomIn} onZoomOut={onZoomOut} onFitToView={onFitToView} />)
    
    fireEvent.click(screen.getByTitle('Zoom In'))
    expect(onZoomIn).toHaveBeenCalled()
    
    fireEvent.click(screen.getByTitle('Zoom Out'))
    expect(onZoomOut).toHaveBeenCalled()
    
    fireEvent.click(screen.getByTitle('Fit to View'))
    expect(onFitToView).toHaveBeenCalled()
  })

  it('renders analyze button', () => {
    render(<EditorToolbar {...defaultProps} />)
    
    expect(screen.getByText(/Analyze/)).toBeInTheDocument()
  })

  it('calls onAnalyze when analyze button is clicked', () => {
    const onAnalyze = vi.fn()
    render(<EditorToolbar {...defaultProps} onAnalyze={onAnalyze} />)
    
    fireEvent.click(screen.getByText(/Analyze/))
    expect(onAnalyze).toHaveBeenCalled()
  })
})

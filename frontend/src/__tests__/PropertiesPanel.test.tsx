import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import PropertiesPanel from '../components/PropertiesPanel'
import { StructuralModel, Node, Member } from '../types/model'

describe('PropertiesPanel', () => {
  const mockModel: StructuralModel = {
    nodes: [
      { id: 'N1', x: 0, y: 0, support: 'pin' },
      { id: 'N2', x: 100, y: 0, support: 'none' },
      { id: 'N3', x: 50, y: 50, support: 'roller', loads: { fx: 10, fy: -5 } },
    ],
    members: [
      { id: 'M1', startNodeId: 'N1', endNodeId: 'N2', material: 'steel' },
      { id: 'M2', startNodeId: 'N2', endNodeId: 'N3', material: 'aluminum' },
    ],
  }

  const defaultProps = {
    model: mockModel,
    selectedNode: null,
    selectedMember: null,
    onUpdateNode: vi.fn(),
    onUpdateMember: vi.fn(),
  }

  it('shows model stats when nothing is selected', () => {
    render(<PropertiesPanel {...defaultProps} />)
    
    expect(screen.getByText('Model Summary')).toBeInTheDocument()
    expect(screen.getByText(/Nodes:/)).toBeInTheDocument()
    expect(screen.getByText(/Members:/)).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument() // 3 nodes
    const membersAndSupports = screen.getAllByText('2')
    expect(membersAndSupports.length).toBeGreaterThanOrEqual(1) // 2 members, 2 supports
  })

  it('shows node properties when node is selected', () => {
    const selectedNode: Node = mockModel.nodes[0]
    render(<PropertiesPanel {...defaultProps} selectedNode={selectedNode} />)
    
    expect(screen.getByText(/Node N1/)).toBeInTheDocument()
    expect(screen.getByLabelText(/X Coordinate/)).toHaveValue(0)
    expect(screen.getByLabelText(/Y Coordinate/)).toHaveValue(0)
  })

  it('shows support type dropdown for selected node', () => {
    const selectedNode: Node = mockModel.nodes[0]
    render(<PropertiesPanel {...defaultProps} selectedNode={selectedNode} />)
    
    const supportSelect = screen.getByLabelText(/Support Type/)
    expect(supportSelect).toBeInTheDocument()
    expect(supportSelect).toHaveValue('pin')
  })

  it('calls onUpdateNode when coordinates are changed', () => {
    const onUpdateNode = vi.fn()
    const selectedNode: Node = mockModel.nodes[0]
    render(<PropertiesPanel {...defaultProps} selectedNode={selectedNode} onUpdateNode={onUpdateNode} />)
    
    const xInput = screen.getByLabelText(/X Coordinate/)
    fireEvent.change(xInput, { target: { value: '25' } })
    
    expect(onUpdateNode).toHaveBeenCalledWith('N1', { x: 25 })
  })

  it('calls onUpdateNode when support type is changed', () => {
    const onUpdateNode = vi.fn()
    const selectedNode: Node = mockModel.nodes[0]
    render(<PropertiesPanel {...defaultProps} selectedNode={selectedNode} onUpdateNode={onUpdateNode} />)
    
    const supportSelect = screen.getByLabelText(/Support Type/)
    fireEvent.change(supportSelect, { target: { value: 'roller' } })
    
    expect(onUpdateNode).toHaveBeenCalledWith('N1', { support: 'roller' })
  })

  it('shows load inputs for selected node', () => {
    const selectedNode: Node = mockModel.nodes[2]
    render(<PropertiesPanel {...defaultProps} selectedNode={selectedNode} />)
    
    expect(screen.getByLabelText(/Fx \(kips\)/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Fy \(kips\)/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Fx \(kips\)/)).toHaveValue(10)
    expect(screen.getByLabelText(/Fy \(kips\)/)).toHaveValue(-5)
  })

  it('calls onUpdateNode when load values are changed', () => {
    const onUpdateNode = vi.fn()
    const selectedNode: Node = mockModel.nodes[0]
    render(<PropertiesPanel {...defaultProps} selectedNode={selectedNode} onUpdateNode={onUpdateNode} />)
    
    const fxInput = screen.getByLabelText(/Fx \(kips\)/)
    fireEvent.change(fxInput, { target: { value: '15' } })
    
    expect(onUpdateNode).toHaveBeenCalledWith('N1', { loads: { fx: 15, fy: 0 } })
  })

  it('shows member properties when member is selected', () => {
    const selectedMember: Member = mockModel.members[0]
    render(<PropertiesPanel {...defaultProps} selectedMember={selectedMember} />)
    
    expect(screen.getByText(/Member M1/)).toBeInTheDocument()
    expect(screen.getByText(/Start Node:/)).toBeInTheDocument()
    expect(screen.getByText('N1')).toBeInTheDocument()
    expect(screen.getByText(/End Node:/)).toBeInTheDocument()
    expect(screen.getByText('N2')).toBeInTheDocument()
  })

  it('shows member length for selected member', () => {
    const selectedMember: Member = mockModel.members[0]
    render(<PropertiesPanel {...defaultProps} selectedMember={selectedMember} />)
    
    expect(screen.getByText(/Length:/)).toBeInTheDocument()
    expect(screen.getByText(/100.00 ft/)).toBeInTheDocument()
  })

  it('shows material dropdown for selected member', () => {
    const selectedMember: Member = mockModel.members[0]
    render(<PropertiesPanel {...defaultProps} selectedMember={selectedMember} />)
    
    const materialSelect = screen.getByLabelText(/Material/)
    expect(materialSelect).toBeInTheDocument()
    expect(materialSelect).toHaveValue('steel')
  })

  it('calls onUpdateMember when material is changed', () => {
    const onUpdateMember = vi.fn()
    const selectedMember: Member = mockModel.members[0]
    render(<PropertiesPanel {...defaultProps} selectedMember={selectedMember} onUpdateMember={onUpdateMember} />)
    
    const materialSelect = screen.getByLabelText(/Material/)
    fireEvent.change(materialSelect, { target: { value: 'wood' } })
    
    expect(onUpdateMember).toHaveBeenCalledWith('M1', { material: 'wood' })
  })

  it('shows cross-section info for selected member', () => {
    const selectedMember: Member = mockModel.members[0]
    render(<PropertiesPanel {...defaultProps} selectedMember={selectedMember} />)
    
    expect(screen.getByText(/Cross-Section/)).toBeInTheDocument()
    expect(screen.getByText(/W8x24/)).toBeInTheDocument()
  })

  it('calculates total length correctly', () => {
    render(<PropertiesPanel {...defaultProps} />)
    
    // Member 1: sqrt((100-0)^2 + (0-0)^2) = 100
    // Member 2: sqrt((50-100)^2 + (50-0)^2) = sqrt(2500 + 2500) = 70.71
    // Total: 170.71
    expect(screen.getByText(/170.71 ft/)).toBeInTheDocument()
  })

  it('counts supports correctly', () => {
    render(<PropertiesPanel {...defaultProps} />)
    
    // 2 nodes with supports (pin and roller)
    const rows = screen.getAllByText('2')
    // One for members count, one for supports count
    expect(rows.length).toBeGreaterThanOrEqual(2)
  })

  it('counts loaded nodes correctly', () => {
    render(<PropertiesPanel {...defaultProps} />)
    
    // Only N3 has loads
    expect(screen.getByText('1')).toBeInTheDocument()
  })
})

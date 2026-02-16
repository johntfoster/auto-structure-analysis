import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import ResultsVisualization from '../components/ResultsVisualization'

describe('ResultsVisualization', () => {
  const mockNodes = [
    {
      id: 1,
      x: 0,
      y: 0,
      support_type: 'pin',
      reaction_x: 1000,
      reaction_y: 2000,
      displacement_x: 0,
      displacement_y: 0,
    },
    {
      id: 2,
      x: 100,
      y: 0,
      support_type: 'roller',
      reaction_x: 0,
      reaction_y: 1500,
      displacement_x: 0.5,
      displacement_y: -1.2,
    },
    {
      id: 3,
      x: 50,
      y: 100,
      support_type: null,
      displacement_x: 0.3,
      displacement_y: -2.5,
    },
  ]

  const mockMembers = [
    {
      id: 1,
      start_node: 1,
      end_node: 2,
      axial_force: 5000,
      stress: 10.0,
      stress_ratio: 0.05,
    },
    {
      id: 2,
      start_node: 2,
      end_node: 3,
      axial_force: -3000,
      stress: 6.0,
      stress_ratio: 0.85,
    },
    {
      id: 3,
      start_node: 3,
      end_node: 1,
      axial_force: 4000,
      stress: 8.0,
      stress_ratio: 1.2,
    },
  ]

  const mockLoads = [
    {
      node_id: 3,
      fx: 0,
      fy: -10000,
    },
  ]

  it('renders without crashing', () => {
    render(
      <ResultsVisualization
        nodes={mockNodes}
        members={mockMembers}
        loads={mockLoads}
      />
    )
    
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeTruthy()
  })

  it('renders with empty data', () => {
    render(
      <ResultsVisualization
        nodes={[]}
        members={[]}
        loads={[]}
      />
    )
    
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeTruthy()
  })

  it('renders with stress visualization enabled', () => {
    render(
      <ResultsVisualization
        nodes={mockNodes}
        members={mockMembers}
        loads={mockLoads}
        showStress={true}
        showForces={false}
      />
    )
    
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeTruthy()
  })

  it('renders with force visualization enabled', () => {
    render(
      <ResultsVisualization
        nodes={mockNodes}
        members={mockMembers}
        loads={mockLoads}
        showStress={false}
        showForces={true}
      />
    )
    
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeTruthy()
  })

  it('renders with deformed shape enabled', () => {
    render(
      <ResultsVisualization
        nodes={mockNodes}
        members={mockMembers}
        loads={mockLoads}
        showDeformed={true}
        deformationScale={50}
      />
    )
    
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeTruthy()
  })

  it('renders with different deformation scale', () => {
    render(
      <ResultsVisualization
        nodes={mockNodes}
        members={mockMembers}
        loads={mockLoads}
        showDeformed={true}
        deformationScale={100}
      />
    )
    
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeTruthy()
  })

  it('handles nodes without displacement data', () => {
    const nodesWithoutDisplacement = mockNodes.map(node => ({
      ...node,
      displacement_x: undefined,
      displacement_y: undefined,
    }))
    
    render(
      <ResultsVisualization
        nodes={nodesWithoutDisplacement}
        members={mockMembers}
        loads={mockLoads}
        showDeformed={true}
      />
    )
    
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeTruthy()
  })

  it('handles different support types', () => {
    const nodesWithDifferentSupports = [
      { ...mockNodes[0], support_type: 'pin' },
      { ...mockNodes[1], support_type: 'roller' },
      { ...mockNodes[2], support_type: 'fixed' },
    ]
    
    render(
      <ResultsVisualization
        nodes={nodesWithDifferentSupports}
        members={mockMembers}
        loads={mockLoads}
      />
    )
    
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeTruthy()
  })

  it('handles members with different stress ratios', () => {
    const membersWithVaryingStress = [
      { ...mockMembers[0], stress_ratio: 0.5 },  // Safe (green)
      { ...mockMembers[1], stress_ratio: 0.85 }, // Warning (yellow)
      { ...mockMembers[2], stress_ratio: 1.2 },  // Failure (red)
    ]
    
    render(
      <ResultsVisualization
        nodes={mockNodes}
        members={membersWithVaryingStress}
        loads={mockLoads}
        showStress={true}
      />
    )
    
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeTruthy()
  })

  it('handles loads with horizontal and vertical components', () => {
    const loadsWithBothComponents = [
      { node_id: 1, fx: 5000, fy: 0 },
      { node_id: 2, fx: 0, fy: -3000 },
      { node_id: 3, fx: 2000, fy: -4000 },
    ]
    
    render(
      <ResultsVisualization
        nodes={mockNodes}
        members={mockMembers}
        loads={loadsWithBothComponents}
      />
    )
    
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeTruthy()
  })

  it('handles zero-force members', () => {
    const membersWithZeroForce = [
      { ...mockMembers[0], axial_force: 0, stress: 0, stress_ratio: 0 },
      { ...mockMembers[1], axial_force: 5000, stress: 10, stress_ratio: 0.5 },
    ]
    
    render(
      <ResultsVisualization
        nodes={mockNodes}
        members={membersWithZeroForce}
        loads={mockLoads}
      />
    )
    
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeTruthy()
  })

  it('renders with all visualization options enabled', () => {
    render(
      <ResultsVisualization
        nodes={mockNodes}
        members={mockMembers}
        loads={mockLoads}
        showDeformed={true}
        showStress={true}
        showForces={true}
        deformationScale={75}
      />
    )
    
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeTruthy()
  })

  it('renders with all visualization options disabled', () => {
    render(
      <ResultsVisualization
        nodes={mockNodes}
        members={mockMembers}
        loads={mockLoads}
        showDeformed={false}
        showStress={false}
        showForces={false}
      />
    )
    
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeTruthy()
  })
})

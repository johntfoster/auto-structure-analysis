import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../App'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(screen.getByText(/Analyze Structures from Photos/i)).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    render(<App />)
    expect(screen.getByText(/Home/i)).toBeInTheDocument()
    expect(screen.getByText(/Capture/i)).toBeInTheDocument()
    expect(screen.getByText(/History/i)).toBeInTheDocument()
    expect(screen.getByText(/Settings/i)).toBeInTheDocument()
  })

  it('renders the home page by default', () => {
    render(<App />)
    expect(screen.getByText(/Get Started/i)).toBeInTheDocument()
  })
})

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../App'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(screen.getByText(/Snap. Analyze. Build with confidence./i)).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    render(<App />)
    // Use getAllByText for links that might appear multiple times
    const homeLinks = screen.getAllByText(/Home/i)
    expect(homeLinks.length).toBeGreaterThan(0)
    
    expect(screen.getAllByRole('link', { name: /Capture/i }).length).toBeGreaterThan(0)
    expect(screen.getAllByRole('link', { name: /History/i }).length).toBeGreaterThan(0)
    expect(screen.getAllByRole('link', { name: /Settings/i }).length).toBeGreaterThan(0)
  })

  it('renders the home page by default', () => {
    render(<App />)
    expect(screen.getByText(/Get Started/i)).toBeInTheDocument()
  })
})

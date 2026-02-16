import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Home from '../pages/Home'
import Capture from '../pages/Capture'
import Analyze from '../pages/Analyze'
import History from '../pages/History'
import Settings from '../pages/Settings'

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('Page Components', () => {
  describe('Home', () => {
    it('renders without crashing', () => {
      renderWithRouter(<Home />)
      expect(screen.getByText(/Analyze Structures from Photos/i)).toBeInTheDocument()
    })

    it('displays Get Started link', () => {
      renderWithRouter(<Home />)
      expect(screen.getByText(/Get Started/i)).toBeInTheDocument()
    })
  })

  describe('Capture', () => {
    it('renders without crashing', () => {
      renderWithRouter(<Capture />)
      expect(screen.getByRole('heading', { name: /Capture Structure/i })).toBeInTheDocument()
    })

    it('displays file upload input', () => {
      renderWithRouter(<Capture />)
      const fileInput = document.querySelector('input[type="file"]')
      expect(fileInput).toBeTruthy()
    })
  })

  describe('Analyze', () => {
    it('renders without crashing', () => {
      renderWithRouter(<Analyze />)
      expect(screen.getByRole('heading', { name: /Analysis Results/i })).toBeInTheDocument()
    })
  })

  describe('History', () => {
    it('renders without crashing', () => {
      renderWithRouter(<History />)
      expect(screen.getByRole('heading', { name: /Analysis History/i })).toBeInTheDocument()
    })
  })

  describe('Settings', () => {
    it('renders without crashing', () => {
      renderWithRouter(<Settings />)
      expect(screen.getByRole('heading', { name: /Settings/i })).toBeInTheDocument()
    })
  })
})

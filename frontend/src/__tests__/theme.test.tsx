import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider, useTheme } from '../contexts/ThemeContext'
import ThemeToggle from '../components/ThemeToggle'

// Test component that uses the theme
function TestComponent() {
  const { theme, resolvedTheme } = useTheme()
  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <span data-testid="resolved-theme">{resolvedTheme}</span>
    </div>
  )
}

describe('ThemeContext', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
  })

  it('provides default theme as system', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    )

    expect(screen.getByTestId('theme').textContent).toBe('system')
  })

  it('resolves system theme to light by default', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    )

    expect(screen.getByTestId('resolved-theme').textContent).toBe('light')
  })

  it('persists theme to localStorage', () => {
    function TestWithToggle() {
      const { setTheme } = useTheme()
      return (
        <div>
          <TestComponent />
          <button onClick={() => setTheme('dark')}>Set Dark</button>
        </div>
      )
    }

    render(
      <ThemeProvider>
        <TestWithToggle />
      </ThemeProvider>
    )

    fireEvent.click(screen.getByText('Set Dark'))

    expect(localStorage.getItem('theme')).toBe('dark')
    expect(screen.getByTestId('theme').textContent).toBe('dark')
  })

  it('applies dark class to document when dark theme', () => {
    function TestWithToggle() {
      const { setTheme } = useTheme()
      return <button onClick={() => setTheme('dark')}>Set Dark</button>
    }

    render(
      <ThemeProvider>
        <TestWithToggle />
      </ThemeProvider>
    )

    fireEvent.click(screen.getByText('Set Dark'))

    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })
})

describe('ThemeToggle', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
  })

  it('renders theme toggle button', () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    )

    const button = screen.getByRole('button', { name: /toggle theme/i })
    expect(button).toBeInTheDocument()
  })

  it('cycles through light -> dark -> system', () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
        <TestComponent />
      </ThemeProvider>
    )

    const button = screen.getByRole('button', { name: /toggle theme/i })

    // Start at system (default)
    expect(screen.getByTestId('theme').textContent).toBe('system')

    // Click to set light (system -> light)
    fireEvent.click(button)
    expect(screen.getByTestId('theme').textContent).toBe('light')

    // Click to set dark
    fireEvent.click(button)
    expect(screen.getByTestId('theme').textContent).toBe('dark')

    // Click to set system
    fireEvent.click(button)
    expect(screen.getByTestId('theme').textContent).toBe('system')
  })
})

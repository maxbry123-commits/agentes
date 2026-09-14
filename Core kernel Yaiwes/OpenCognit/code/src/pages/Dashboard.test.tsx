import { describe, it, expect, vi } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/render'
import { Dashboard } from './Dashboard'

vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocketEvent: () => {},
  useWebSocketStatus: () => false,
}))

describe('Dashboard page', () => {
  it('renders without crashing and shows dashboard heading', async () => {
    render(<Dashboard />)
    await waitFor(() => {
      expect(screen.getByText(/Dashboard/i)).toBeInTheDocument()
    })
  })
})

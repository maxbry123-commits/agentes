import { describe, it, expect } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/render'
import { Tasks } from './Tasks'

describe('Tasks page', () => {
  it('renders without crashing and shows tasks heading', async () => {
    render(<Tasks />)
    await waitFor(() => {
      expect(screen.getByText(/Kanban/i)).toBeInTheDocument()
    })
  })
})

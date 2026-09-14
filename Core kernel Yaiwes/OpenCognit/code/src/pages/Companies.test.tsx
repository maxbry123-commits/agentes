import { describe, it, expect } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/render'
import { Companies } from './Companies'

describe('Companies page', () => {
  it('renders without crashing and shows companies heading', async () => {
    render(<Companies />)
    await waitFor(() => {
      expect(screen.getByText(/Start a new AI company/i)).toBeInTheDocument()
    })
  })
})

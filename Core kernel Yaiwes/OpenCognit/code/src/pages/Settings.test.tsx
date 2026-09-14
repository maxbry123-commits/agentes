import { describe, it, expect } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/render'
import { Settings } from './Settings'

describe('Settings page', () => {
  it('renders without crashing', async () => {
    render(<Settings />)
    await waitFor(() => {
      expect(screen.getByText(/Configure your OpenCognit instance/i)).toBeInTheDocument()
    })
  })
})

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import React from 'react'

function Hello({ name }: { name: string }) {
  return <div>Hello {name}</div>
}

describe('Frontend test setup smoke test', () => {
  it('renders a React component with Testing Library', () => {
    render(<Hello name="OpenCognit" />)
    expect(screen.getByText('Hello OpenCognit')).toBeInTheDocument()
  })
})

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { request, ApiError } from './client'

describe('API Client', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should attach Authorization header when token exists', async () => {
    localStorage.setItem('opencognit_token', 'test-token')
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    )

    await request('/test')

    expect(fetchSpy).toHaveBeenCalledWith(
      '/api/test',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
          'Content-Type': 'application/json',
        }),
      })
    )
  })

  it('should throw ApiError on non-ok response', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify({ error: 'Bad Request' }), { status: 400, headers: { 'Content-Type': 'application/json' } })
      )
    )

    await expect(request('/test')).rejects.toThrow(ApiError)
    await expect(request('/test')).rejects.toThrow('Bad Request')
  })

  it('should throw generic ApiError when response body is not json', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('Internal Server Error', { status: 500 })
    )

    await expect(request('/test')).rejects.toThrow('HTTP 500')
  })

  it('ApiError should expose status and body', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'missing field' }), { status: 422, headers: { 'Content-Type': 'application/json' } })
    )

    try {
      await request('/test')
      expect.fail('should have thrown')
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError)
      expect((err as ApiError).status).toBe(422)
      expect((err as ApiError).body).toEqual({ detail: 'missing field' })
    }
  })
})

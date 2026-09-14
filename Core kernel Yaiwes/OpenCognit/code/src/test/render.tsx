import React from 'react'
import { render as rtlRender } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { I18nProvider } from '@/i18n'
import { CompanyProvider } from '@/hooks/useCompany'
import { BreadcrumbProvider } from '@/hooks/useBreadcrumbs'
import { ToastProvider } from '@/components/ToastProvider'

const testQueryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false, staleTime: Infinity },
  },
})

export function render(ui: React.ReactElement, { client = testQueryClient } = {}) {
  return rtlRender(
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <I18nProvider>
          <ToastProvider>
            <BreadcrumbProvider>
              <CompanyProvider>{ui}</CompanyProvider>
            </BreadcrumbProvider>
          </ToastProvider>
        </I18nProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

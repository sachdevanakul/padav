import { describe, expect, it } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from '../app/App'

function renderApp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={['/onboarding']}><App /></MemoryRouter></QueryClientProvider>)
}

describe('onboarding experience', () => {
  it('moves through the three preparation steps', async () => {
    const user = userEvent.setup()
    renderApp()
    expect(screen.getByRole('heading', { name: /learn smart/i })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /continue/i }))
    expect(await screen.findByRole('heading', { name: /prepare\.\s*practice/i })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /continue/i }))
    await waitFor(() => expect(screen.getAllByRole('heading').map((heading) => heading.textContent).join(' ')).toMatch(/your success/i))
    expect(screen.getByRole('button', { name: /start your journey/i })).toBeInTheDocument()
  })
})

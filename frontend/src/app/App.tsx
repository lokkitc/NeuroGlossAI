import { BrowserRouter } from 'react-router-dom'
import { AppProviders } from './providers'
import { AppRouter } from './router'

export function App() {
  const routerFutureFlags = {
    v7_startTransition: true,
    v7_relativeSplatPath: true,
  } as const

  return (
    <AppProviders>
      <BrowserRouter future={routerFutureFlags as unknown as Record<string, boolean>}>
        <AppRouter />
      </BrowserRouter>
    </AppProviders>
  )
}

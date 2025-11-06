import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/index.css'
import App from './App.tsx'

// Log the configured WebSocket URL so devs can verify the client will connect to the right server
console.log('VITE_WS_URL=', import.meta.env.VITE_WS_URL)

const rootEl = document.getElementById('root')
if (!rootEl) {
  throw new Error('Root element with id "root" not found')
}

createRoot(rootEl).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

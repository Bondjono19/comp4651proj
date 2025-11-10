import { useState } from 'react'
import './styles/app.css'
import ChatRoom from './components/ChatRoom'

export default function App() {
  const [username, setUsername] = useState(() => `guest${Math.floor(Math.random() * 900) + 100}`)

  return (
    // make the app a full-viewport flex column so ChatRoom can fill the screen
    <div className="app-root">
      <header className="chat-header">
        <h1>Chatroom</h1>
        <div style={{ marginLeft: 'auto' }}>
          <label className="chat-username">
            Username:{' '}
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </label>
        </div>
      </header>

      <main className="chat-main">
        <ChatRoom user={username} />
      </main>
    </div>
  )
}

import { useState, useEffect } from 'react';
import './styles/app.css';
import ChatRoom from './components/ChatRoom';
import AuthForm from './components/AuthForm';
import authService from './services/authService';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [showAuthForm, setShowAuthForm] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already authenticated
    const checkAuth = async () => {
      if (authService.isAuthenticated()) {
        const valid = await authService.verify();
        if (valid) {
          setIsAuthenticated(true);
          setUsername(authService.getUsername() || '');
        } else {
          // Token invalid, set guest username
          setUsername(`guest${Math.floor(Math.random() * 10000)}`);
        }
      } else {
        // Not authenticated, set guest username
        const storedGuest = localStorage.getItem('guest_username');
        if (storedGuest) {
          setUsername(storedGuest);
        } else {
          const guestName = `guest${Math.floor(Math.random() * 10000)}`;
          setUsername(guestName);
          localStorage.setItem('guest_username', guestName);
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const handleAuthSuccess = (authenticatedUsername: string) => {
    setUsername(authenticatedUsername);
    setIsAuthenticated(true);
    setShowAuthForm(false);
    // Remove guest username from localStorage
    localStorage.removeItem('guest_username');
  };

  const handleLogout = () => {
    authService.logout();
    setIsAuthenticated(false);
    setShowAuthForm(false);
    // Generate new guest username
    const guestName = `guest${Math.floor(Math.random() * 10000)}`;
    setUsername(guestName);
    localStorage.setItem('guest_username', guestName);
  };

  const handleShowAuth = () => {
    setShowAuthForm(true);
  };

  const handleCancelAuth = () => {
    setShowAuthForm(false);
  };

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontSize: '1.2rem',
        color: '#667eea'
      }}>
        Loading...
      </div>
    );
  }

  if (showAuthForm) {
    return <AuthForm onAuthSuccess={handleAuthSuccess} onCancel={handleCancelAuth} />;
  }

  return (
    <div className="app-root">
      <header className="chat-header">
        <h1>Chatroom</h1>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '15px' }}>
          {isAuthenticated ? (
            <>
              <span className="chat-username">
                <span style={{ color: '#28a745', marginRight: '5px' }}>●</span>
                <strong>{username}</strong>
              </span>
              <button 
                onClick={handleLogout}
                className="header-button logout-button"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <span className="chat-username">
                <span style={{ color: '#ffc107', marginRight: '5px' }}>●</span>
                {username}
                <span style={{ fontSize: '0.8rem', marginLeft: '5px', color: '#888' }}>(guest)</span>
              </span>
              <button 
                onClick={handleShowAuth}
                className="header-button login-button"
              >
                Login / Register
              </button>
            </>
          )}
        </div>
      </header>

      <main className="chat-main">
        <ChatRoom user={username} />
      </main>
    </div>
  );
}

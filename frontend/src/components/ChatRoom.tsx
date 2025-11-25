import { useEffect, useRef, useState } from 'react';
import ChatService from '../services/chatService';
import type { Message } from '../types/message';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import '../styles/chatroom.css';

// Available rooms
const ROOMS = [
  { id: 'general', name: 'General Chat' },
  { id: 'python', name: 'Python' },
  { id: 'devops', name: 'DevOps' },
  { id: 'random', name: 'Random' }
];

export default function ChatRoom({ user = 'guest' }: { user?: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentRoom, setCurrentRoom] = useState('general');
  const [isGuest] = useState(user.startsWith('guest'));
  const serviceRef = useRef<ChatService | null>(null);

  useEffect(() => {
    const service = new ChatService();
    serviceRef.current = service;
    service.connect(user, currentRoom);
    const unsub = service.onMessage((m) => {
      setMessages((s) => [...s, m]);
    });
    return () => {
      unsub();
      service.close();
    };
  }, [user]); // Only depend on user, not room

  // Function to switch rooms
  const switchRoom = (roomId: string) => {
    if (roomId === currentRoom) return; // Don't switch to same room
    
    console.log(`Switching from ${currentRoom} to ${roomId}`);
    setCurrentRoom(roomId);
    setMessages([]); // Clear messages for the new room
    
    // Send join message for the new room
    serviceRef.current?.joinRoom(roomId, user);
  };

  const send = (text: string) => {
    serviceRef.current?.sendMessage(text);
  };

  return (
    <div className="chatroom">
      {/* Room Selection Header */}
      <div className="room-selector">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3>Room: {currentRoom}</h3>
          {isGuest && (
            <div style={{ 
              fontSize: '0.85rem', 
              color: '#888',
              background: '#fff3cd',
              padding: '4px 12px',
              borderRadius: '4px',
              border: '1px solid #ffc107'
            }}>
              👤 Guest Mode
            </div>
          )}
        </div>
        <div className="room-buttons">
          {ROOMS.map(room => (
            <button
              key={room.id}
              onClick={() => switchRoom(room.id)}
              className={currentRoom === room.id ? 'active' : ''}
            >
              {room.name}
            </button>
          ))}
        </div>
      </div>

      <MessageList messages={messages} />
      <MessageInput onSend={send} />
    </div>
  );
}
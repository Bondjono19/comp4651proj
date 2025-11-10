import type { Message } from '../types/message';

type MessageHandler = (message: Message) => void;

export default class ChatService {
	private ws: WebSocket | null = null;
	private handlers: MessageHandler[] = [];
	private reconnectDelay = 1000;
	private shouldReconnect = true;
	private url: string;
	private clientId: string;
	private currentUsername: string = '';

	constructor() {
		this.clientId = this.generateClientId();
		this.url = `ws://localhost:8000/ws/${this.clientId}`;
	}

	private generateClientId(): string {
		return 'client_' + Math.random().toString(36).substr(2, 9);
	}

	connect(username: string, roomId: string = 'general') {
		this.shouldReconnect = true;
		this.currentUsername = username;
		if (this.ws) this.ws.close();
		this.createSocket(username, roomId);
	}

	private createSocket(username: string, roomId: string) {
		this.ws = new WebSocket(this.url);

		this.ws.addEventListener('open', () => {
			console.log('Connected to chat server: ', this.url);
			this.reconnectDelay = 1000;
			
			// Send join room message immediately after connection
			const joinMessage = {
				roomId: roomId,
				username: username
			};
			this.ws?.send(JSON.stringify(joinMessage));
			console.log('Sent join message:', joinMessage);
		});	

		this.ws.addEventListener('message', (event) => {
			try {
				const message: Message = JSON.parse(event.data);
				console.log('Received message:', message);
				this.handlers.forEach((handler) => handler(message));
			} catch (error) {
				console.error('Error parsing message: ', error);
			}
		});

		this.ws.addEventListener('close', () => {
			if (!this.shouldReconnect) return;
			console.log('Disconnected from chat server: ', this.url);
			setTimeout(() => this.createSocket(this.currentUsername, 'general'), this.reconnectDelay);
			this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
		});

		this.ws.addEventListener('error', (error) => {
			console.error('WebSocket error: ', error);
			this.ws?.close();
		});
	}

	sendMessage(content: string) {
		if (this.ws && this.ws.readyState === WebSocket.OPEN) {
			// Send in the format your backend expects for chat messages
			const chatMessage = {
				content: content
				// Don't include id, username, timestamp - backend will add them
			};
			this.ws.send(JSON.stringify(chatMessage));
			console.log('Sent chat message:', chatMessage);
		} else {
			console.error('WebSocket is not open. Unable to send message.');
		}
	}

	joinRoom(roomId: string, username: string) {
		this.currentUsername = username;
		if (this.ws && this.ws.readyState === WebSocket.OPEN) {
			const joinMessage = {
				roomId: roomId,
				username: username
			};
			this.ws.send(JSON.stringify(joinMessage));
			console.log('Sent room join:', joinMessage);
		} else {
			// If websocket not ready, reconnect with new room
			this.connect(username, roomId);
		}
	}

	onMessage(handler: MessageHandler) {
		this.handlers.push(handler);
		return () => {
			this.handlers = this.handlers.filter((h) => h !== handler);
		};
	}

	close() {
		this.shouldReconnect = false;
		this.ws?.close();
		this.ws = null;
	}
}
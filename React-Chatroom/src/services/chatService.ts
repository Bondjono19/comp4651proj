import type { Message } from '../types/message';

type MessageHandler = (message: Message) => void;

export default class ChatService {
	private ws: WebSocket | null = null;
	private handlers: MessageHandler[] = [];
	private reconnectDelay = 1000; // Initial reconnect delay in ms
	private shouldReconnect = true;

	private url: string;

	constructor(url: string) {
		this.url = url;
	}

	connect() {
		this.shouldReconnect = true;
		if (this.ws) this.ws.close();
		this.createSocket();
	};

	private createSocket() {
		this.ws = new WebSocket(this.url);

		this.ws.addEventListener('open', () => {
			console.log('Connected to chat server: ', this.url);
			this.reconnectDelay = 1000; // Reset delay on successful connection
		});	

		this.ws.addEventListener('message', (event) => {
			try {
				const message: Message = JSON.parse(event.data);
				this.handlers.forEach((handler) => handler(message));
			} catch (error) {
				console.error('Error parsing message: ', error);
			}
		});

		this.ws.addEventListener('close', () => {
			if (!this.shouldReconnect) return;
			console.log('Disconnected from chat server: ', this.url);
			setTimeout(() => this.createSocket(), this.reconnectDelay);
			this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000); // Exponential backoff up to 30s
		});

		this.ws.addEventListener('error', (error) => {
			console.error('WebSocket error: ', error);
			this.ws?.close();
		});
	}

	sendMessage(message: Message) {
		if (this.ws && this.ws.readyState === WebSocket.OPEN) {
			this.ws.send(JSON.stringify(message));
		} else {
			console.error('WebSocket is not open. Unable to send message.');
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
};
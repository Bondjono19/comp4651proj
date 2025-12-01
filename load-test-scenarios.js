import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// Custom metrics
const messagesSent = new Counter('messages_sent');
const messagesReceived = new Counter('messages_received');
const messageLatency = new Trend('message_latency');

// Configuration - Update these with your actual endpoints
const WEBSOCKET_URL = __ENV.WS_URL || 'ws://localhost:8000/ws';
const ROOM_LIST = ['general', 'python', 'devops', 'random'];

// Scenario selection via environment variable
const SCENARIO = __ENV.SCENARIO || 'baseline';

// Scenario configurations
export const scenarios = {
  // Scenario 1: Baseline Performance
  baseline: {
    executor: 'ramping-vus',
    stages: [
      { duration: '30s', target: 50 },
      { duration: '2m', target: 50 },
      { duration: '30s', target: 100 },
      { duration: '2m', target: 100 },
      { duration: '30s', target: 200 },
      { duration: '2m', target: 200 },
      { duration: '1m', target: 0 },
    ],
    gracefulRampDown: '30s',
  },
  
  // Scenario 2: Horizontal Scaling Test
  scaling: {
    executor: 'ramping-vus',
    stages: [
      { duration: '1m', target: 200 },
      { duration: '5m', target: 200 },
      { duration: '1m', target: 500 },
      { duration: '5m', target: 500 },
      { duration: '1m', target: 1000 },
      { duration: '5m', target: 1000 },
      { duration: '2m', target: 0 },
    ],
    gracefulRampDown: '1m',
  },
  
  // Scenario 3: Burst Traffic
  burst: {
    executor: 'ramping-vus',
    stages: [
      { duration: '30s', target: 50 },    // Warm up
      { duration: '2m', target: 500 },    // Rapid spike
      { duration: '3m', target: 500 },    // Sustain
      { duration: '1m', target: 50 },     // Cool down
      { duration: '30s', target: 0 },
    ],
    gracefulRampDown: '30s',
  },
  
  // Scenario 4: Multi-Room Concurrent
  multiroom: {
    executor: 'constant-vus',
    vus: 400,
    duration: '5m',
  },
  
  // Scenario 5: Long-Duration Stability
  stability: {
    executor: 'constant-vus',
    vus: 200,
    duration: '30m',
  },
};

// Select scenario
export const options = {
  scenarios: {
    [SCENARIO]: scenarios[SCENARIO],
  },
  thresholds: {
    'ws_connecting': ['p(95)<1000'], // 95% of connections should complete within 1s
    'ws_msgs_received': ['count>0'],
    'message_latency': ['p(95)<200', 'p(99)<500'], // Latency thresholds
  },
};

export default function () {
  const userId = `user_${__VU}_${Date.now()}`;
  const room = ROOM_LIST[Math.floor(Math.random() * ROOM_LIST.length)];
  
  // Backend expects /ws/{client_id} format
  const url = `${WEBSOCKET_URL}/${userId}`;
  const params = { tags: { scenario: SCENARIO, room: room } };
  
  const res = ws.connect(url, params, function (socket) {
    let messageCount = 0;
    const sentMessages = new Map();
    
    socket.on('open', () => {
      console.log(`VU ${__VU}: Connected to ${room} room`);
      
      // Join room - backend expects roomId (not room_id)
      const joinMsg = JSON.stringify({
        roomId: room,
        username: userId,
      });
      socket.send(joinMsg);
      
      // Send messages at configured interval
      const messageInterval = SCENARIO === 'burst' ? 2000 : 5000;
      
      socket.setInterval(() => {
        const msgId = `${userId}_${messageCount++}`;
        const timestamp = Date.now();
        
        // Backend expects 'content' field for messages
        const message = JSON.stringify({
          content: `Test message ${messageCount} from ${userId}`,
          msg_id: msgId,
          timestamp: timestamp,
        });
        
        sentMessages.set(msgId, timestamp);
        socket.send(message);
        messagesSent.add(1);
        
        // Clean up old messages from map (prevent memory leak)
        if (sentMessages.size > 100) {
          const oldestKey = sentMessages.keys().next().value;
          sentMessages.delete(oldestKey);
        }
      }, messageInterval);
    });
    
    socket.on('message', (data) => {
      try {
        const msg = JSON.parse(data);
        messagesReceived.add(1);
        
        // Calculate latency if this is our own message
        if (msg.msg_id && sentMessages.has(msg.msg_id)) {
          const latency = Date.now() - sentMessages.get(msg.msg_id);
          messageLatency.add(latency);
          sentMessages.delete(msg.msg_id);
        }
        
        check(msg, {
          'message has content': (m) => m.content !== undefined || m.type !== undefined,
        });
      } catch (e) {
        console.error(`VU ${__VU}: Failed to parse message:`, e);
      }
    });
    
    socket.on('close', () => {
      console.log(`VU ${__VU}: Disconnected from ${room} room`);
    });
    
    socket.on('error', (e) => {
      console.error(`VU ${__VU}: WebSocket error:`, e);
    });
    
    // Keep connection alive for scenario duration
    const duration = SCENARIO === 'stability' ? 1800000 : 300000; // 30min or 5min
    socket.setTimeout(() => {
      socket.close();
    }, duration);
  });
  
  check(res, {
    'connection established': (r) => r && r.status === 101,
  });
}

export function handleSummary(data) {
  return {
    'summary.json': JSON.stringify(data),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}

function textSummary(data, options) {
  const indent = options.indent || '';
  const enableColors = options.enableColors || false;
  
  let summary = `\n${indent}Test Summary - Scenario: ${SCENARIO}\n`;
  summary += `${indent}${'='.repeat(50)}\n\n`;
  
  // Extract key metrics
  const metrics = data.metrics;
  
  if (metrics.ws_connecting) {
    summary += `${indent}WebSocket Connection Time:\n`;
    summary += `${indent}  avg: ${metrics.ws_connecting.values.avg.toFixed(2)}ms\n`;
    if (metrics.ws_connecting.values['p(95)']) {
      summary += `${indent}  p95: ${metrics.ws_connecting.values['p(95)'].toFixed(2)}ms\n`;
    }
  }
  
  if (metrics.message_latency) {
    summary += `${indent}Message Latency:\n`;
    summary += `${indent}  avg: ${metrics.message_latency.values.avg.toFixed(2)}ms\n`;
    if (metrics.message_latency.values['p(95)']) {
      summary += `${indent}  p95: ${metrics.message_latency.values['p(95)'].toFixed(2)}ms\n`;
    }
    if (metrics.message_latency.values['p(99)']) {
      summary += `${indent}  p99: ${metrics.message_latency.values['p(99)'].toFixed(2)}ms\n`;
    }
  }
  
  if (metrics.messages_sent) {
    summary += `${indent}Messages Sent: ${metrics.messages_sent.values.count}\n`;
  }
  
  if (metrics.messages_received) {
    summary += `${indent}Messages Received: ${metrics.messages_received.values.count}\n`;
  }
  
  if (metrics.http_req_failed && metrics.http_req_failed.values.rate !== undefined) {
    const failRate = metrics.http_req_failed.values.rate * 100;
    summary += `${indent}Failure Rate: ${failRate.toFixed(2)}%\n`;
  }
  
  summary += `\n${indent}${'='.repeat(50)}\n`;
  
  return summary;
}
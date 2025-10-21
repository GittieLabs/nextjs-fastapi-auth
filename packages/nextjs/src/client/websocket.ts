/**
 * WebSocket authentication utilities
 *
 * Provides utilities for creating authenticated WebSocket connections
 * with automatic token refresh and reconnection.
 */

'use client'

import type { SupabaseClient } from '@supabase/supabase-js'

export interface WebSocketAuthOptions {
  /** Supabase client for getting auth token */
  supabase: SupabaseClient
  /** WebSocket URL */
  url: string
  /** Protocols to use */
  protocols?: string | string[]
  /** Auto-reconnect on disconnect */
  autoReconnect?: boolean
  /** Reconnect delay in ms */
  reconnectDelay?: number
  /** Maximum reconnect attempts */
  maxReconnectAttempts?: number
  /** Enable debug logging */
  debug?: boolean
  /** Callback when connection opens */
  onOpen?: (event: Event) => void
  /** Callback when connection closes */
  onClose?: (event: CloseEvent) => void
  /** Callback when error occurs */
  onError?: (event: Event) => void
  /** Callback when message received */
  onMessage?: (event: MessageEvent) => void
}

/**
 * Create an authenticated WebSocket connection
 *
 * Automatically includes Supabase JWT token in query parameters
 * and handles reconnection with token refresh.
 *
 * @param options - WebSocket configuration options
 * @returns WebSocket instance
 *
 * @example
 * ```typescript
 * const ws = await createAuthenticatedWebSocket({
 *   supabase,
 *   url: 'ws://localhost:8000/ws/updates',
 *   onMessage: (event) => {
 *     console.log('Message:', JSON.parse(event.data))
 *   }
 * })
 * ```
 */
export async function createAuthenticatedWebSocket(
  options: WebSocketAuthOptions
): Promise<WebSocket> {
  const {
    supabase,
    url,
    protocols,
    autoReconnect = true,
    reconnectDelay = 5000,
    maxReconnectAttempts = 5,
    debug = false,
    onOpen,
    onClose,
    onError,
    onMessage,
  } = options

  let reconnectAttempts = 0
  let ws: WebSocket | null = null
  let manualClose = false

  async function connect(): Promise<WebSocket> {
    try {
      // Get current session token
      const { data: { session }, error } = await supabase.auth.getSession()

      if (error || !session?.access_token) {
        throw new Error('No active session for WebSocket authentication')
      }

      // Append token to URL as query parameter
      const wsUrl = new URL(url)
      wsUrl.searchParams.set('token', session.access_token)

      if (debug) {
        console.log('[WebSocket] Connecting to:', wsUrl.toString().replace(session.access_token, '[TOKEN]'))
      }

      // Create WebSocket connection
      ws = new WebSocket(wsUrl.toString(), protocols)

      // Setup event handlers
      ws.addEventListener('open', (event) => {
        if (debug) {
          console.log('[WebSocket] ✅ Connection opened')
        }
        reconnectAttempts = 0 // Reset reconnect attempts on successful connection
        if (onOpen) onOpen(event)
      })

      ws.addEventListener('close', (event) => {
        if (debug) {
          console.log('[WebSocket] Connection closed:', event.code, event.reason)
        }

        if (onClose) onClose(event)

        // Attempt reconnection if not manually closed
        if (!manualClose && autoReconnect && reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++
          if (debug) {
            console.log(`[WebSocket] Reconnecting in ${reconnectDelay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})`)
          }
          setTimeout(() => connect(), reconnectDelay)
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          console.error('[WebSocket] Max reconnect attempts reached')
        }
      })

      ws.addEventListener('error', (event) => {
        console.error('[WebSocket] Error:', event)
        if (onError) onError(event)
      })

      ws.addEventListener('message', (event) => {
        if (debug) {
          console.log('[WebSocket] Message received:', event.data)
        }
        if (onMessage) onMessage(event)
      })

      return ws

    } catch (error) {
      console.error('[WebSocket] Connection error:', error)
      throw error
    }
  }

  const websocket = await connect()

  // Add close method that prevents auto-reconnect
  const originalClose = websocket.close.bind(websocket)
  websocket.close = (code?: number, reason?: string) => {
    manualClose = true
    originalClose(code, reason)
  }

  return websocket
}

/**
 * WebSocket connection manager with automatic token refresh
 */
export class AuthenticatedWebSocketManager {
  private ws: WebSocket | null = null
  private options: WebSocketAuthOptions
  private reconnectTimer: NodeJS.Timeout | null = null
  private heartbeatTimer: NodeJS.Timeout | null = null
  private manualClose = false
  private reconnectAttempts = 0

  constructor(options: WebSocketAuthOptions) {
    this.options = {
      autoReconnect: true,
      reconnectDelay: 5000,
      maxReconnectAttempts: 5,
      debug: false,
      ...options
    }
  }

  /**
   * Connect to WebSocket
   */
  async connect(): Promise<void> {
    this.ws = await createAuthenticatedWebSocket(this.options)
    this.startHeartbeat()
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    this.manualClose = true
    this.stopHeartbeat()
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  /**
   * Send message through WebSocket
   */
  send(data: string | object): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected')
    }

    const message = typeof data === 'string' ? data : JSON.stringify(data)
    this.ws.send(message)
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }

  /**
   * Get current WebSocket instance
   */
  getWebSocket(): WebSocket | null {
    return this.ws
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    // Send ping every 30 seconds
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'ping' })
      }
    }, 30000)
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }
}

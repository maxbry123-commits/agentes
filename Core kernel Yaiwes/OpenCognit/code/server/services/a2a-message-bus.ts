// A2A Message Bus — Agent-to-Agent messaging layer
// Direct messages, broadcasts, channel posts, and request/response threads.

import { db } from '../db/client.js';
import { agentMessages, agents } from '../db/schema.js';
import { eq, and, isNull, desc, sql, inArray } from 'drizzle-orm';
import { appEvents } from '../events.js';
import { v4 as uuid } from 'uuid';
import { wakeupService } from './wakeup.js';

export interface A2AMessage {
  id: string;
  companyId: string;
  senderId: string;
  senderName?: string;
  recipientId: string | null;
  channel: string | null;
  threadId: string | null;
  type: 'direct' | 'broadcast' | 'channel' | 'request' | 'response';
  payload: { text: string; metadata?: Record<string, unknown>; urgency?: 'low' | 'normal' | 'high' };
  readAt: string | null;
  createdAt: string;
}

export interface SendMessageParams {
  companyId: string;
  senderId: string;
  recipientId?: string;
  channel?: string;
  threadId?: string;
  type?: A2AMessage['type'];
  payload: A2AMessage['payload'];
  shouldWakeup?: boolean;
}

export interface InboxOptions {
  unreadOnly?: boolean;
  limit?: number;
  since?: string; // ISO timestamp
}

export interface A2AMessageBus {
  sendMessage(params: SendMessageParams): Promise<A2AMessage>;
  getInbox(agentId: string, opts?: InboxOptions): Promise<A2AMessage[]>;
  getThread(threadId: string): Promise<A2AMessage[]>;
  markAsRead(messageIds: string[]): Promise<number>;
  getUnreadCount(agentId: string): Promise<number>;
  broadcastToChannel(companyId: string, channel: string, senderId: string, payload: A2AMessage['payload']): Promise<A2AMessage>;
  sendResponse(requestMessageId: string, senderId: string, payload: A2AMessage['payload']): Promise<A2AMessage | null>;
}

function parsePayload(raw: string): A2AMessage['payload'] {
  try {
    return JSON.parse(raw);
  } catch {
    return { text: raw };
  }
}

class A2AMessageBusImpl implements A2AMessageBus {
  async sendMessage(params: SendMessageParams): Promise<A2AMessage> {
    const now = new Date().toISOString();
    const id = uuid();

    const msg = {
      id,
      companyId: params.companyId,
      senderId: params.senderId,
      recipientId: params.recipientId || null,
      channel: params.channel || null,
      threadId: params.threadId || null,
      type: params.type || 'direct',
      payload: JSON.stringify(params.payload),
      readAt: null,
      createdAt: now,
    };

    db.insert(agentMessages).values(msg).run();

    const message: A2AMessage = {
      ...msg,
      payload: params.payload,
      readAt: null,
    };

    // Enrich with sender name for broadcast
    const sender = db.select({ name: agents.name }).from(agents).where(eq(agents.id, params.senderId)).get();
    if (sender) message.senderName = sender.name;

    // Broadcast real-time update
    appEvents.emit('broadcast', {
      type: 'agent_message',
      data: message,
    });

    // Optionally wake recipient
    if (params.shouldWakeup !== false && params.recipientId && params.recipientId !== params.senderId) {
      wakeupService.wakeup(params.recipientId, params.companyId, {
        source: 'assignment',
        triggerDetail: 'mention',
        reason: `A2A message from ${sender?.name || 'agent'}`,
        payload: { messageId: id, type: params.type },
      }).catch(() => {});
    }

    return message;
  }

  async getInbox(agentId: string, opts: InboxOptions = {}): Promise<A2AMessage[]> {
    const { unreadOnly = false, limit = 50, since } = opts;

    const agent = db.select({ companyId: agents.companyId }).from(agents).where(eq(agents.id, agentId)).get();
    if (!agent) return [];

    const conditions: any[] = [
      eq(agentMessages.companyId, agent.companyId),
    ];

    if (unreadOnly) {
      conditions.push(isNull(agentMessages.readAt));
    }

    if (since) {
      conditions.push(sql`${agentMessages.createdAt} > ${since}`);
    }

    // Direct messages to this agent OR broadcasts (recipientId IS NULL) OR channel messages
    // We exclude messages sent BY this agent unless they are in a thread
    const rows = db.select()
      .from(agentMessages)
      .where(
        and(
          ...conditions,
          sql`(
            ${agentMessages.recipientId} = ${agentId}
            OR ${agentMessages.recipientId} IS NULL
            OR ${agentMessages.senderId} = ${agentId}
          )`
        )
      )
      .orderBy(desc(agentMessages.createdAt), desc(sql`rowid`))
      .limit(limit)
      .all();

    return this.enrichRows(rows as any[]);
  }

  async getThread(threadId: string): Promise<A2AMessage[]> {
    const rows = db.select()
      .from(agentMessages)
      .where(eq(agentMessages.threadId, threadId))
      .orderBy(agentMessages.createdAt)
      .all();

    return this.enrichRows(rows as any[]);
  }

  async markAsRead(messageIds: string[]): Promise<number> {
    if (messageIds.length === 0) return 0;
    const now = new Date().toISOString();

    const result = db.update(agentMessages)
      .set({ readAt: now })
      .where(inArray(agentMessages.id, messageIds))
      .run();

    return result.changes || 0;
  }

  async getUnreadCount(agentId: string): Promise<number> {
    const agent = db.select({ companyId: agents.companyId }).from(agents).where(eq(agents.id, agentId)).get();
    if (!agent) return 0;

    const result = db.select({ count: sql<number>`count(*)` })
      .from(agentMessages)
      .where(
        and(
          eq(agentMessages.companyId, agent.companyId),
          eq(agentMessages.recipientId, agentId),
          isNull(agentMessages.readAt)
        )
      )
      .get();

    return result?.count || 0;
  }

  async broadcastToChannel(
    companyId: string,
    channel: string,
    senderId: string,
    payload: A2AMessage['payload']
  ): Promise<A2AMessage> {
    return this.sendMessage({
      companyId,
      senderId,
      channel,
      type: 'channel',
      payload,
      shouldWakeup: false,
    });
  }

  async sendResponse(
    requestMessageId: string,
    senderId: string,
    payload: A2AMessage['payload']
  ): Promise<A2AMessage | null> {
    const request = db.select()
      .from(agentMessages)
      .where(eq(agentMessages.id, requestMessageId))
      .get() as any;

    if (!request) return null;

    const threadId = request.threadId || requestMessageId;
    const recipientId = request.senderId;
    const companyId = request.companyId;

    return this.sendMessage({
      companyId,
      senderId,
      recipientId,
      threadId,
      type: 'response',
      payload,
      shouldWakeup: true,
    });
  }

  private enrichRows(rows: any[]): A2AMessage[] {
    const senderIds = [...new Set(rows.map(r => r.senderId))];
    const senderMap = new Map<string, string>();

    for (const id of senderIds) {
      const a = db.select({ name: agents.name }).from(agents).where(eq(agents.id, id)).get();
      senderMap.set(id, a?.name || 'Unknown');
    }

    return rows.map(r => ({
      id: r.id,
      companyId: r.companyId,
      senderId: r.senderId,
      senderName: senderMap.get(r.senderId) || 'Unknown',
      recipientId: r.recipientId,
      channel: r.channel,
      threadId: r.threadId,
      type: r.type,
      payload: parsePayload(r.payload),
      readAt: r.readAt,
      createdAt: r.createdAt,
    }));
  }
}

export const a2aMessageBus: A2AMessageBus = new A2AMessageBusImpl();

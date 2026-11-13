import { describe, it, expect, beforeEach } from 'vitest';
import { a2aMessageBus } from './a2a-message-bus.js';
import { db } from '../db/client.js';
import { companies, agents } from '../db/schema.js';
import { v4 as uuid } from 'uuid';
import { resetTestDb } from '../__tests__/setup.js';

const now = () => new Date().toISOString();

function createTestCompany(name = 'Test Co') {
  const id = uuid();
  db.insert(companies).values({ id, name, status: 'active', createdAt: now(), updatedAt: now() }).run();
  return id;
}

function createTestAgent(companyId: string, name: string) {
  const id = uuid();
  db.insert(agents).values({
    id,
    companyId,
    name,
    role: 'Tester',
    status: 'active',
    createdAt: now(),
    updatedAt: now(),
  }).run();
  return id;
}

describe('a2aMessageBus', () => {
  let companyId: string;
  let aliceId: string;
  let bobId: string;

  beforeEach(() => {
    resetTestDb();
    companyId = createTestCompany();
    aliceId = createTestAgent(companyId, 'Alice');
    bobId = createTestAgent(companyId, 'Bob');
  });

  it('sends a direct message', async () => {
    const msg = await a2aMessageBus.sendMessage({
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      payload: { text: 'Hello Bob!' },
    });

    expect(msg.id).toBeTruthy();
    expect(msg.senderId).toBe(aliceId);
    expect(msg.recipientId).toBe(bobId);
    expect(msg.payload.text).toBe('Hello Bob!');
    expect(msg.type).toBe('direct');
    expect(msg.readAt).toBeNull();
  });

  it('lists inbox for recipient', async () => {
    await a2aMessageBus.sendMessage({
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      payload: { text: 'Message 1' },
    });
    await a2aMessageBus.sendMessage({
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      payload: { text: 'Message 2' },
    });

    const inbox = await a2aMessageBus.getInbox(bobId);
    expect(inbox.length).toBe(2);
    expect(inbox[0].payload.text).toBe('Message 2'); // newest first
    expect(inbox[1].payload.text).toBe('Message 1');
  });

  it('inbox excludes messages for other agents', async () => {
    const charlieId = createTestAgent(companyId, 'Charlie');
    await a2aMessageBus.sendMessage({
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      payload: { text: 'For Bob' },
    });

    const inbox = await a2aMessageBus.getInbox(charlieId);
    expect(inbox.length).toBe(0);
  });

  it('returns unread count', async () => {
    await a2aMessageBus.sendMessage({
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      payload: { text: 'Unread' },
    });

    const count = await a2aMessageBus.getUnreadCount(bobId);
    expect(count).toBe(1);

    const inbox = await a2aMessageBus.getInbox(bobId);
    await a2aMessageBus.markAsRead([inbox[0].id]);

    const countAfter = await a2aMessageBus.getUnreadCount(bobId);
    expect(countAfter).toBe(0);
  });

  it('filters inbox by unreadOnly', async () => {
    const msg = await a2aMessageBus.sendMessage({
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      payload: { text: 'Unread msg' },
    });
    await a2aMessageBus.markAsRead([msg.id]);
    await a2aMessageBus.sendMessage({
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      payload: { text: 'Still unread' },
    });

    const unread = await a2aMessageBus.getInbox(bobId, { unreadOnly: true });
    expect(unread.length).toBe(1);
    expect(unread[0].payload.text).toBe('Still unread');
  });

  it('supports threaded messages', async () => {
    const threadId = uuid();
    await a2aMessageBus.sendMessage({
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      threadId,
      payload: { text: 'Thread start' },
    });
    await a2aMessageBus.sendMessage({
      companyId,
      senderId: bobId,
      recipientId: aliceId,
      threadId,
      payload: { text: 'Thread reply' },
    });

    const thread = await a2aMessageBus.getThread(threadId);
    expect(thread.length).toBe(2);
    expect(thread[0].payload.text).toBe('Thread start');
    expect(thread[1].payload.text).toBe('Thread reply');
  });

  it('broadcasts to channel', async () => {
    const msg = await a2aMessageBus.broadcastToChannel(
      companyId,
      '#dev-team',
      aliceId,
      { text: 'Deploy at 3pm' }
    );

    expect(msg.channel).toBe('#dev-team');
    expect(msg.type).toBe('channel');
    expect(msg.recipientId).toBeNull();

    // Both agents should see the broadcast in their inbox
    const aliceInbox = await a2aMessageBus.getInbox(aliceId);
    const bobInbox = await a2aMessageBus.getInbox(bobId);
    expect(aliceInbox.some(m => m.id === msg.id)).toBe(true);
    expect(bobInbox.some(m => m.id === msg.id)).toBe(true);
  });

  it('sends a response to a request', async () => {
    const request = await a2aMessageBus.sendMessage({
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      type: 'request',
      payload: { text: 'Need the API key' },
    });

    const response = await a2aMessageBus.sendResponse(
      request.id,
      bobId,
      { text: 'Here: sk-1234' }
    );

    expect(response).not.toBeNull();
    expect(response!.type).toBe('response');
    expect(response!.recipientId).toBe(aliceId);
    expect(response!.threadId).toBe(request.id);
  });

  it('returns null when responding to non-existent request', async () => {
    const response = await a2aMessageBus.sendResponse(
      'non-existent-id',
      bobId,
      { text: 'Whatever' }
    );
    expect(response).toBeNull();
  });

  it('enriches sender name in messages', async () => {
    const msg = await a2aMessageBus.sendMessage({
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      payload: { text: 'Hi' },
    });

    expect(msg.senderName).toBe('Alice');
  });

  it('filters inbox by since timestamp', async () => {
    const oldMsg = await a2aMessageBus.sendMessage({
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      payload: { text: 'Old' },
    });

    await new Promise(r => setTimeout(r, 50));
    const since = new Date().toISOString();
    await new Promise(r => setTimeout(r, 50));

    await a2aMessageBus.sendMessage({
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      payload: { text: 'New' },
    });

    const inbox = await a2aMessageBus.getInbox(bobId, { since });
    expect(inbox.length).toBe(1);
    expect(inbox[0].payload.text).toBe('New');
  });

  it('does not include messages from other companies', async () => {
    const otherCompanyId = createTestCompany('Other Co');
    const otherAgentId = createTestAgent(otherCompanyId, 'Other');

    await a2aMessageBus.sendMessage({
      companyId: otherCompanyId,
      senderId: otherAgentId,
      recipientId: otherAgentId,
      payload: { text: 'Other company msg' },
    });

    const inbox = await a2aMessageBus.getInbox(bobId);
    expect(inbox.some(m => m.payload.text === 'Other company msg')).toBe(false);
  });

  it('bulk mark as read works', async () => {
    const msg1 = await a2aMessageBus.sendMessage({
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      payload: { text: 'One' },
    });
    const msg2 = await a2aMessageBus.sendMessage({
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      payload: { text: 'Two' },
    });

    const changed = await a2aMessageBus.markAsRead([msg1.id, msg2.id]);
    expect(changed).toBe(2);

    const count = await a2aMessageBus.getUnreadCount(bobId);
    expect(count).toBe(0);
  });

  it('respects shouldWakeup=false', async () => {
    const msg = await a2aMessageBus.sendMessage({
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      payload: { text: 'No wakeup' },
      shouldWakeup: false,
    });

    expect(msg.payload.text).toBe('No wakeup');
    // Just verify it doesn't throw; wakeup is a side-effect we can't easily spy here
  });

  it('includes broadcast in sender inbox', async () => {
    await a2aMessageBus.broadcastToChannel(
      companyId,
      '#all',
      aliceId,
      { text: 'All hands' }
    );

    const aliceInbox = await a2aMessageBus.getInbox(aliceId);
    expect(aliceInbox.some(m => m.payload.text === 'All hands')).toBe(true);
  });

  it('limits inbox results', async () => {
    for (let i = 0; i < 5; i++) {
      await a2aMessageBus.sendMessage({
        companyId,
        senderId: aliceId,
        recipientId: bobId,
        payload: { text: `Msg ${i}` },
        shouldWakeup: false,
      });
    }
    const inbox = await a2aMessageBus.getInbox(bobId, { limit: 2 });
    expect(inbox.length).toBe(2);
  });

  it('parses payload with metadata', async () => {
    const msg = await a2aMessageBus.sendMessage({
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      payload: { text: 'With meta', metadata: { key: 'value', num: 42 } },
      shouldWakeup: false,
    });
    expect(msg.payload.metadata).toEqual({ key: 'value', num: 42 });

    const inbox = await a2aMessageBus.getInbox(bobId);
    const found = inbox.find(m => m.id === msg.id);
    expect(found?.payload.metadata).toEqual({ key: 'value', num: 42 });
  });

  it('handles malformed payload gracefully', async () => {
    // Insert raw malformed payload directly
    const id = 'bad-payload-id';
    const { db } = await import('../db/client.js');
    const { agentMessages } = await import('../db/schema.js');
    db.insert(agentMessages).values({
      id,
      companyId,
      senderId: aliceId,
      recipientId: bobId,
      type: 'direct',
      payload: 'not-json-at-all',
      createdAt: new Date().toISOString(),
    }).run();

    const inbox = await a2aMessageBus.getInbox(bobId);
    const found = inbox.find(m => m.id === id);
    expect(found).toBeTruthy();
    expect(found!.payload.text).toBe('not-json-at-all');
  });

  it('thread includes only messages with matching threadId', async () => {
    const threadA = 'thread-a';
    const threadB = 'thread-b';
    await a2aMessageBus.sendMessage({ companyId, senderId: aliceId, recipientId: bobId, threadId: threadA, payload: { text: 'A1' }, shouldWakeup: false });
    await a2aMessageBus.sendMessage({ companyId, senderId: bobId, recipientId: aliceId, threadId: threadA, payload: { text: 'A2' }, shouldWakeup: false });
    await a2aMessageBus.sendMessage({ companyId, senderId: aliceId, recipientId: bobId, threadId: threadB, payload: { text: 'B1' }, shouldWakeup: false });

    const thread = await a2aMessageBus.getThread(threadA);
    expect(thread.length).toBe(2);
    expect(thread.every(m => m.threadId === threadA)).toBe(true);
  });

  it('markAsRead returns 0 for empty array', async () => {
    const changed = await a2aMessageBus.markAsRead([]);
    expect(changed).toBe(0);
  });
});

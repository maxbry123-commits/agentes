import { request } from './core';

export const apiNodes = {
  liste: () => request<Array<{ id: string; capabilities: string[]; registeredAt: string; lastSeen: string }>>('/nodes/status'),
};

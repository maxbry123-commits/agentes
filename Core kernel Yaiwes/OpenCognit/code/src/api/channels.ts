import { request } from './core';

export const apiChannels = {
  status: () => request<Array<{ id: string; name: string; icon: string; status: { connected: boolean; lastActivity?: string; error?: string } }>>('/channels/status'),
};

import { create } from 'zustand';
import { wsClient } from '../api/websocket';

export interface TodoItem {
  id: string;
  content: string;
  status: 'pending' | 'in_progress' | 'completed';
  children?: TodoItem[];
}

interface TodoStore {
  items: TodoItem[];
  planName: string | null;
  visible: boolean;
  setItems: (items: TodoItem[], planName?: string | null) => void;
  toggleVisible: () => void;
}

export const useTodoStore = create<TodoStore>((set) => ({
  items: [],
  planName: null,
  visible: true,
  setItems: (items, planName) => set({ items, planName: planName ?? null }),
  toggleVisible: () => set((s) => ({ visible: !s.visible })),
}));

// Listen for todo-related tool results that carry todo state
wsClient.on('tool_result', (message) => {
  const d = message.data;
  if (!d) return;

  const toolName = d.tool_name;
  if (toolName === 'write_todos' || toolName === 'update_todo' || toolName === 'complete_todo' || toolName === 'clear_todos') {
    // If the backend sends todo state in the result, update store
    if (d.todos) {
      const items: TodoItem[] = (d.todos || []).map((t: any) => ({
        id: t.id || String(Math.random()),
        content: t.content || t.title || '',
        status: t.status || 'pending',
        children: t.children?.map((c: any) => ({
          id: c.id || String(Math.random()),
          content: c.content || c.title || '',
          status: c.status || 'pending',
        })),
      }));
      useTodoStore.getState().setItems(items, d.plan_name);
    }
  }
});

// Listen for status updates that may carry todo data
wsClient.on('status_update', (message) => {
  const d = message.data;
  if (!d?.todos) return;

  const items: TodoItem[] = (d.todos || []).map((t: any) => ({
    id: t.id || String(Math.random()),
    content: t.content || t.title || '',
    status: t.status || 'pending',
    children: t.children?.map((c: any) => ({
      id: c.id || String(Math.random()),
      content: c.content || c.title || '',
      status: c.status || 'pending',
    })),
  }));
  useTodoStore.getState().setItems(items, d.plan_name);
});

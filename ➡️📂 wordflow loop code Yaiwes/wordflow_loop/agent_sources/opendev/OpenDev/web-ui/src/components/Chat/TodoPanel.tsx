import { useTodoStore, type TodoItem } from '../../stores/todo';

function statusIcon(status: string): string {
  switch (status) {
    case 'completed': return '✓';
    case 'in_progress': return '→';
    default: return '○';
  }
}

function statusColor(status: string): string {
  switch (status) {
    case 'completed': return 'text-yellow-400';
    case 'in_progress': return 'text-accent-100';
    default: return 'text-text-400';
  }
}

function TodoItemRow({ item, indent = 0 }: { item: TodoItem; indent?: number }) {
  return (
    <>
      <div
        className="flex items-start gap-2 py-0.5 font-mono text-sm leading-6"
        style={{ paddingLeft: `${indent * 16 + 8}px` }}
      >
        <span className={`shrink-0 w-4 text-center ${statusColor(item.status)}`}>
          {item.status === 'in_progress' ? (
            <span className="inline-block w-3 h-3 border-2 border-accent-100/60 border-t-transparent rounded-full animate-spin" />
          ) : (
            statusIcon(item.status)
          )}
        </span>
        <span className={`${
          item.status === 'completed' ? 'text-text-400 line-through' :
          item.status === 'in_progress' ? 'text-text-200' :
          'text-text-300'
        }`}>
          {item.content}
        </span>
      </div>
      {item.children?.map((child) => (
        <TodoItemRow key={child.id} item={child} indent={indent + 1} />
      ))}
    </>
  );
}

export function TodoPanel() {
  const items = useTodoStore((s) => s.items);
  const planName = useTodoStore((s) => s.planName);
  const visible = useTodoStore((s) => s.visible);
  const toggleVisible = useTodoStore((s) => s.toggleVisible);

  if (items.length === 0) return null;

  const completed = items.filter((i) => i.status === 'completed').length;
  const total = items.length;
  const allDone = completed === total;

  return (
    <div className={`border-b shrink-0 ${
      allDone ? 'border-green-700/30 bg-green-950/10' : 'border-border-300/30 bg-bg-100/50'
    }`}>
      {/* Header */}
      <button
        onClick={toggleVisible}
        className="w-full flex items-center gap-2 px-4 py-2 text-xs font-mono text-text-300 hover:text-text-200 transition-colors"
      >
        <span className={`font-semibold uppercase tracking-wide ${allDone ? 'text-green-400' : 'text-text-200'}`}>
          TODOS{planName ? `: ${planName}` : ''}
        </span>
        <span className="text-text-400">({completed}/{total})</span>
        <div className="flex-1" />
        <span className="text-text-400 text-[10px]">{visible ? '▼' : '▶'}</span>
      </button>

      {/* Items */}
      {visible && (
        <div className="px-2 pb-2">
          {items.map((item) => (
            <TodoItemRow key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}

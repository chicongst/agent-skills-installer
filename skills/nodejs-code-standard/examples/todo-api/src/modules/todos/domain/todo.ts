export const TODO_STATUSES = ['open', 'done'] as const;
export const TODO_PRIORITIES = ['low', 'medium', 'high'] as const;

export type TodoStatus = (typeof TODO_STATUSES)[number];
export type TodoPriority = (typeof TODO_PRIORITIES)[number];

export interface Todo {
  readonly id: string;
  readonly title: string;
  readonly description: string | null;
  readonly dueDate: string | null;
  readonly priority: TodoPriority | null;
  readonly status: TodoStatus;
  readonly completedAt: string | null;
  readonly version: number;
  readonly createdAt: string;
  readonly updatedAt: string;
}

export interface TodoDraft {
  readonly title: string;
  readonly description?: string | null;
  readonly dueDate?: string | null;
  readonly priority?: TodoPriority | null;
}

export type TodoChanges = Partial<TodoDraft>;

export function createTodo(draft: TodoDraft, id: string, now: Date): Todo {
  const timestamp = now.toISOString();
  return {
    id,
    title: draft.title.trim(),
    description: cleanText(draft.description),
    dueDate: draft.dueDate ?? null,
    priority: draft.priority ?? null,
    status: 'open',
    completedAt: null,
    version: 1,
    createdAt: timestamp,
    updatedAt: timestamp,
  };
}

export function applyChanges(todo: Todo, changes: TodoChanges, now: Date): Todo {
  return touch(
    {
      ...todo,
      title: changes.title === undefined ? todo.title : changes.title.trim(),
      description: changes.description === undefined ? todo.description : cleanText(changes.description),
      dueDate: changes.dueDate === undefined ? todo.dueDate : changes.dueDate,
      priority: changes.priority === undefined ? todo.priority : changes.priority,
    },
    now,
  );
}

export function markDone(todo: Todo, now: Date): Todo {
  if (todo.status === 'done') return todo;
  return touch({ ...todo, status: 'done', completedAt: now.toISOString() }, now);
}

export function reopen(todo: Todo, now: Date): Todo {
  if (todo.status === 'open') return todo;
  return touch({ ...todo, status: 'open', completedAt: null }, now);
}

function touch(todo: Todo, now: Date): Todo {
  return { ...todo, version: todo.version + 1, updatedAt: now.toISOString() };
}

function cleanText(value: string | null | undefined): string | null {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

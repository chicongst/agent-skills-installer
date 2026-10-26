import type { Todo } from '../domain/todo.ts';
import { TodoNotFoundError, TodoVersionMismatchError } from '../domain/todo.errors.ts';
import type { TodoRepository, WriteResult } from './ports/todo.repository.ts';

export async function loadForWrite(todos: TodoRepository, id: string, expectedVersion: number): Promise<Todo> {
  const todo = await todos.findById(id);
  if (!todo) throw new TodoNotFoundError(id);
  if (todo.version !== expectedVersion) throw new TodoVersionMismatchError(todo.version);
  return todo;
}

export async function assertWritten(todos: TodoRepository, id: string, result: WriteResult): Promise<void> {
  if (result === 'written') return;
  if (result === 'not_found') throw new TodoNotFoundError(id);

  const latest = await todos.findById(id);
  if (!latest) throw new TodoNotFoundError(id);
  throw new TodoVersionMismatchError(latest.version);
}

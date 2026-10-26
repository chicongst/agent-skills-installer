import type { Page, PageRequest } from '../../../../shared/pagination/page.ts';
import type { Todo, TodoStatus } from '../../domain/todo.ts';

export type TodoSortField = 'createdAt' | 'dueDate';

export interface TodoSort {
  readonly field: TodoSortField;
  readonly direction: 'asc' | 'desc';
}

export interface TodoListQuery extends PageRequest {
  readonly status?: TodoStatus | undefined;
  readonly search?: string | undefined;
  readonly sort: TodoSort;
}

export type WriteResult = 'written' | 'not_found' | 'version_mismatch';

export interface TodoRepository {
  findById(id: string): Promise<Todo | undefined>;
  list(query: TodoListQuery): Promise<Page<Todo>>;
  insert(todo: Todo): Promise<void>;
  update(todo: Todo, expectedVersion: number): Promise<WriteResult>;
  delete(id: string, expectedVersion: number): Promise<WriteResult>;
}

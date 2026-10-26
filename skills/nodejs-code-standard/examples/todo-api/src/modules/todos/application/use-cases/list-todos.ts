import type { Page } from '../../../../shared/pagination/page.ts';
import type { Todo } from '../../domain/todo.ts';
import type { TodoListQuery, TodoRepository } from '../ports/todo.repository.ts';

export class ListTodos {
  readonly #todos: TodoRepository;

  constructor(deps: { todos: TodoRepository }) {
    this.#todos = deps.todos;
  }

  execute(query: TodoListQuery): Promise<Page<Todo>> {
    const search = query.search?.trim();
    return this.#todos.list({ ...query, search: search ? search : undefined });
  }
}

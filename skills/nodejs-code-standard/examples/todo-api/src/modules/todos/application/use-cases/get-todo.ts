import type { Todo } from '../../domain/todo.ts';
import { TodoNotFoundError } from '../../domain/todo.errors.ts';
import type { TodoRepository } from '../ports/todo.repository.ts';

export class GetTodo {
  readonly #todos: TodoRepository;

  constructor(deps: { todos: TodoRepository }) {
    this.#todos = deps.todos;
  }

  async execute(id: string): Promise<Todo> {
    const todo = await this.#todos.findById(id);
    if (!todo) throw new TodoNotFoundError(id);
    return todo;
  }
}

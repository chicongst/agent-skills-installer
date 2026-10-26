import type { TodoRepository } from '../ports/todo.repository.ts';
import { assertWritten } from '../versioned-write.ts';

export class DeleteTodo {
  readonly #todos: TodoRepository;

  constructor(deps: { todos: TodoRepository }) {
    this.#todos = deps.todos;
  }

  async execute(id: string, expectedVersion: number): Promise<void> {
    await assertWritten(this.#todos, id, await this.#todos.delete(id, expectedVersion));
  }
}

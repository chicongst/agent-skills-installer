import type { Clock } from '../../../../shared/time/clock.ts';
import { markDone, type Todo } from '../../domain/todo.ts';
import type { TodoRepository } from '../ports/todo.repository.ts';
import { assertWritten, loadForWrite } from '../versioned-write.ts';

export class CompleteTodo {
  readonly #todos: TodoRepository;
  readonly #clock: Clock;

  constructor(deps: { todos: TodoRepository; clock: Clock }) {
    this.#todos = deps.todos;
    this.#clock = deps.clock;
  }

  async execute(id: string, expectedVersion: number): Promise<Todo> {
    const current = await loadForWrite(this.#todos, id, expectedVersion);
    const next = markDone(current, this.#clock.now());
    if (next === current) return current;

    await assertWritten(this.#todos, id, await this.#todos.update(next, expectedVersion));
    return next;
  }
}

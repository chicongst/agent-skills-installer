import type { Clock } from '../../../../shared/time/clock.ts';
import { applyChanges, type Todo, type TodoChanges } from '../../domain/todo.ts';
import type { TodoRepository } from '../ports/todo.repository.ts';
import { assertWritten, loadForWrite } from '../versioned-write.ts';

export interface UpdateTodoCommand {
  readonly id: string;
  readonly expectedVersion: number;
  readonly changes: TodoChanges;
}

export class UpdateTodo {
  readonly #todos: TodoRepository;
  readonly #clock: Clock;

  constructor(deps: { todos: TodoRepository; clock: Clock }) {
    this.#todos = deps.todos;
    this.#clock = deps.clock;
  }

  async execute({ id, expectedVersion, changes }: UpdateTodoCommand): Promise<Todo> {
    const current = await loadForWrite(this.#todos, id, expectedVersion);
    const next = applyChanges(current, changes, this.#clock.now());
    await assertWritten(this.#todos, id, await this.#todos.update(next, expectedVersion));
    return next;
  }
}

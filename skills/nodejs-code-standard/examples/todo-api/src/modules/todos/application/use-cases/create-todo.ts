import type { Clock } from '../../../../shared/time/clock.ts';
import type { IdGenerator } from '../../../../shared/ids/id-generator.ts';
import { createTodo, type Todo, type TodoDraft } from '../../domain/todo.ts';
import type { TodoRepository } from '../ports/todo.repository.ts';

export interface CreateTodoDeps {
  todos: TodoRepository;
  clock: Clock;
  newId: IdGenerator;
}

export class CreateTodo {
  readonly #deps: CreateTodoDeps;

  constructor(deps: CreateTodoDeps) {
    this.#deps = deps;
  }

  async execute(draft: TodoDraft): Promise<Todo> {
    const todo = createTodo(draft, this.#deps.newId(), this.#deps.clock.now());
    await this.#deps.todos.insert(todo);
    return todo;
  }
}

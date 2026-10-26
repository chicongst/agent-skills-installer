import type { IdGenerator } from '../../shared/ids/id-generator.ts';
import type { Clock } from '../../shared/time/clock.ts';
import type { TodoRepository } from './application/ports/todo.repository.ts';
import { CompleteTodo } from './application/use-cases/complete-todo.ts';
import { CreateTodo } from './application/use-cases/create-todo.ts';
import { DeleteTodo } from './application/use-cases/delete-todo.ts';
import { GetTodo } from './application/use-cases/get-todo.ts';
import { ListTodos } from './application/use-cases/list-todos.ts';
import { ReopenTodo } from './application/use-cases/reopen-todo.ts';
import { UpdateTodo } from './application/use-cases/update-todo.ts';

export interface TodoModuleDeps {
  todos: TodoRepository;
  clock: Clock;
  newId: IdGenerator;
}

export interface TodoUseCases {
  readonly create: CreateTodo;
  readonly get: GetTodo;
  readonly list: ListTodos;
  readonly update: UpdateTodo;
  readonly complete: CompleteTodo;
  readonly reopen: ReopenTodo;
  readonly remove: DeleteTodo;
}

export function createTodoUseCases(deps: TodoModuleDeps): TodoUseCases {
  return Object.freeze({
    create: new CreateTodo(deps),
    get: new GetTodo(deps),
    list: new ListTodos(deps),
    update: new UpdateTodo(deps),
    complete: new CompleteTodo(deps),
    reopen: new ReopenTodo(deps),
    remove: new DeleteTodo(deps),
  });
}

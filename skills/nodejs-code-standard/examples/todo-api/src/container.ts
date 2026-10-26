import type { Config, StorageConfig } from './config/env.ts';
import { createPostgresPool } from './shared/database/postgres-pool.ts';
import { uuidGenerator, type IdGenerator } from './shared/ids/id-generator.ts';
import type { Closer } from './shared/lifecycle/process-handlers.ts';
import { systemClock, type Clock } from './shared/time/clock.ts';
import type { TodoRepository } from './modules/todos/application/ports/todo.repository.ts';
import { InMemoryTodoRepository } from './modules/todos/infrastructure/in-memory-todo.repository.ts';
import { PostgresTodoRepository } from './modules/todos/infrastructure/postgres-todo.repository.ts';
import { createTodoUseCases, type TodoUseCases } from './modules/todos/todo.module.ts';

export interface Container {
  readonly todos: TodoUseCases;
  close: Closer;
}

export interface ContainerOverrides {
  clock?: Clock;
  newId?: IdGenerator;
  todoRepository?: TodoRepository;
}

interface Storage {
  todoRepository: TodoRepository;
  close: Closer;
}

export function createContainer(config: Config, overrides: ContainerOverrides = {}): Container {
  const storage: Storage = overrides.todoRepository
    ? { todoRepository: overrides.todoRepository, close: () => Promise.resolve() }
    : createStorage(config.storage);

  const todos = createTodoUseCases({
    todos: storage.todoRepository,
    clock: overrides.clock ?? systemClock,
    newId: overrides.newId ?? uuidGenerator,
  });

  return { todos, close: storage.close };
}

function createStorage(config: StorageConfig): Storage {
  if (config.driver === 'memory') {
    return { todoRepository: new InMemoryTodoRepository(), close: () => Promise.resolve() };
  }

  const pool = createPostgresPool(config.databaseUrl);
  return { todoRepository: new PostgresTodoRepository(pool), close: () => pool.end() };
}

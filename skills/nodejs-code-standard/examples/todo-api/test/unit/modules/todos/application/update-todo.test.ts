import assert from 'node:assert/strict';
import { beforeEach, describe, it } from 'node:test';
import { CreateTodo } from '../../../../../src/modules/todos/application/use-cases/create-todo.ts';
import { UpdateTodo } from '../../../../../src/modules/todos/application/use-cases/update-todo.ts';
import {
  TodoNotFoundError,
  TodoVersionMismatchError,
} from '../../../../../src/modules/todos/domain/todo.errors.ts';
import { InMemoryTodoRepository } from '../../../../../src/modules/todos/infrastructure/in-memory-todo.repository.ts';
import { fixedClock } from '../../../../helpers/fixed-clock.ts';

describe('UpdateTodo', () => {
  let todos: InMemoryTodoRepository;
  let create: CreateTodo;
  let update: UpdateTodo;

  beforeEach(() => {
    todos = new InMemoryTodoRepository();
    const clock = fixedClock();
    create = new CreateTodo({ todos, clock, newId: () => 'todo-1' });
    update = new UpdateTodo({ todos, clock });
  });

  it('persists the change at the next version', async () => {
    await create.execute({ title: 'Buy milk' });

    const updated = await update.execute({ id: 'todo-1', expectedVersion: 1, changes: { title: 'Buy oat milk' } });

    assert.equal(updated.version, 2);
    assert.equal((await todos.findById('todo-1'))?.title, 'Buy oat milk');
  });

  it('rejects a stale version and reports the current one', async () => {
    await create.execute({ title: 'Buy milk' });
    await update.execute({ id: 'todo-1', expectedVersion: 1, changes: { title: 'First' } });

    await assert.rejects(
      update.execute({ id: 'todo-1', expectedVersion: 1, changes: { title: 'Second' } }),
      (err: unknown) => err instanceof TodoVersionMismatchError && err.details?.currentVersion === 2,
    );
  });

  it('lets exactly one of two concurrent writers win', async () => {
    await create.execute({ title: 'Buy milk' });

    const results = await Promise.allSettled([
      update.execute({ id: 'todo-1', expectedVersion: 1, changes: { title: 'User A' } }),
      update.execute({ id: 'todo-1', expectedVersion: 1, changes: { title: 'User B' } }),
    ]);

    assert.deepEqual(results.map((r) => r.status).sort(), ['fulfilled', 'rejected']);
  });

  it('throws not found for an unknown id', async () => {
    await assert.rejects(
      update.execute({ id: 'missing', expectedVersion: 1, changes: { title: 'x' } }),
      TodoNotFoundError,
    );
  });
});

import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { applyChanges, createTodo, markDone, reopen } from '../../../../../src/modules/todos/domain/todo.ts';

const NOW = new Date('2026-01-01T09:00:00.000Z');
const LATER = new Date('2026-01-01T10:00:00.000Z');

describe('todo domain', () => {
  it('creates an open todo at version 1 with trimmed text and null defaults', () => {
    const todo = createTodo({ title: '  Buy milk  ', description: '   ' }, 'id-1', NOW);

    assert.deepEqual(todo, {
      id: 'id-1',
      title: 'Buy milk',
      description: null,
      dueDate: null,
      priority: null,
      status: 'open',
      completedAt: null,
      version: 1,
      createdAt: NOW.toISOString(),
      updatedAt: NOW.toISOString(),
    });
  });

  it('applies only the given changes and bumps the version', () => {
    const todo = createTodo({ title: 'Buy milk', priority: 'low' }, 'id-1', NOW);

    const changed = applyChanges(todo, { priority: null, dueDate: '2026-02-01' }, LATER);

    assert.equal(changed.title, 'Buy milk');
    assert.equal(changed.priority, null);
    assert.equal(changed.dueDate, '2026-02-01');
    assert.equal(changed.version, 2);
    assert.equal(changed.updatedAt, LATER.toISOString());
  });

  it('marks done once and returns the same object when already done', () => {
    const done = markDone(createTodo({ title: 'Buy milk' }, 'id-1', NOW), LATER);

    assert.equal(done.status, 'done');
    assert.equal(done.completedAt, LATER.toISOString());
    assert.equal(markDone(done, LATER), done);
  });

  it('reopens a done todo and clears completedAt', () => {
    const done = markDone(createTodo({ title: 'Buy milk' }, 'id-1', NOW), NOW);

    const reopened = reopen(done, LATER);

    assert.equal(reopened.status, 'open');
    assert.equal(reopened.completedAt, null);
    assert.equal(reopened.version, done.version + 1);
  });
});

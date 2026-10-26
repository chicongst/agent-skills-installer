import assert from 'node:assert/strict';
import { afterEach, beforeEach, describe, it } from 'node:test';
import type { FastifyInstance, LightMyRequestResponse } from 'fastify';
import type { Todo } from '../../../src/modules/todos/domain/todo.ts';
import type { ErrorBody } from '../../../src/shared/http/error-response.ts';
import { buildTestApp } from '../../helpers/test-app.ts';

interface ListBody {
  items: Todo[];
  total: number;
}

describe('todos HTTP API', () => {
  let app: FastifyInstance;

  beforeEach(async () => {
    app = await buildTestApp();
  });

  afterEach(async () => {
    await app.close();
  });

  function send(
    method: 'GET' | 'POST' | 'PATCH' | 'DELETE',
    url: string,
    options: { payload?: Record<string, unknown>; ifMatch?: string } = {},
  ): Promise<LightMyRequestResponse> {
    return app.inject({
      method,
      url,
      ...(options.payload && { payload: options.payload }),
      headers: options.ifMatch === undefined ? {} : { 'if-match': options.ifMatch },
    });
  }

  async function createTodo(payload: Record<string, unknown> = { title: 'Buy milk' }): Promise<Todo> {
    return (await send('POST', '/todos', { payload })).json<Todo>();
  }

  const errorCode = (res: LightMyRequestResponse): string => res.json<ErrorBody>().error.code;

  describe('POST /todos', () => {
    it('returns 201 with location and etag', async () => {
      const res = await send('POST', '/todos', { payload: { title: 'Buy milk', priority: 'high' } });

      assert.equal(res.statusCode, 201);
      const todo = res.json<Todo>();
      assert.equal(res.headers.location, `/todos/${todo.id}`);
      assert.equal(res.headers.etag, '"1"');
      assert.equal(todo.priority, 'high');
    });

    for (const [label, payload] of [
      ['an impossible date', { title: 'x', dueDate: '2026-02-30' }],
      ['an unknown priority', { title: 'x', priority: 'urgent' }],
      ['a numeric title', { title: 123 }],
      ['an unknown field', { title: 'x', status: 'done' }],
    ] as const) {
      it(`rejects ${label} with 400`, async () => {
        const res = await send('POST', '/todos', { payload });

        assert.equal(res.statusCode, 400);
        assert.equal(errorCode(res), 'VALIDATION_FAILED');
      });
    }
  });

  describe('GET /todos', () => {
    it('filters by status, searches the title and sorts by due date with nulls last', async () => {
      await createTodo({ title: 'Milk later', dueDate: '2026-03-01' });
      await createTodo({ title: 'Milk soon', dueDate: '2026-02-01' });
      await createTodo({ title: 'Milk someday' });
      await createTodo({ title: 'Bread' });

      const res = await send('GET', '/todos?status=open&q=milk&sort=dueDate&limit=10');

      const body = res.json<ListBody>();
      assert.equal(body.total, 3);
      assert.deepEqual(
        body.items.map((todo) => todo.title),
        ['Milk soon', 'Milk later', 'Milk someday'],
      );
    });

    it('rejects a limit above 100', async () => {
      const res = await send('GET', '/todos?limit=1000');

      assert.equal(res.statusCode, 400);
    });
  });

  describe('writes with If-Match', () => {
    it('requires If-Match (428)', async () => {
      const todo = await createTodo();

      const res = await send('PATCH', `/todos/${todo.id}`, { payload: { title: 'x' } });

      assert.equal(res.statusCode, 428);
    });

    it('rejects a stale ETag (412) with the current version', async () => {
      const todo = await createTodo();
      await send('PATCH', `/todos/${todo.id}`, { payload: { title: 'First' }, ifMatch: '"1"' });

      const res = await send('PATCH', `/todos/${todo.id}`, { payload: { title: 'Second' }, ifMatch: '"1"' });

      assert.equal(res.statusCode, 412);
      assert.deepEqual(res.json<ErrorBody>().error.details, { currentVersion: 2 });
    });

    it('completes once and treats a repeat as a no-op', async () => {
      const todo = await createTodo();

      const first = await send('POST', `/todos/${todo.id}/complete`, { ifMatch: '"1"' });
      const repeat = await send('POST', `/todos/${todo.id}/complete`, { ifMatch: '"2"' });

      assert.equal(first.json<Todo>().status, 'done');
      assert.equal(repeat.statusCode, 200);
      assert.equal(repeat.headers.etag, '"2"');
    });

    it('deletes with the current version and then returns 404', async () => {
      const todo = await createTodo();

      const deleted = await send('DELETE', `/todos/${todo.id}`, { ifMatch: '"1"' });
      const after = await send('GET', `/todos/${todo.id}`);

      assert.equal(deleted.statusCode, 204);
      assert.equal(after.statusCode, 404);
    });
  });

  it('answers unknown routes in the standard error shape', async () => {
    const res = await send('GET', '/nope');

    assert.equal(res.statusCode, 404);
    assert.equal(errorCode(res), 'ROUTE_NOT_FOUND');
  });
});

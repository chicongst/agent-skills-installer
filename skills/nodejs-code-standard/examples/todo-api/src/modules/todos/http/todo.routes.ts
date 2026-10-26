import type { FastifyPluginCallback, FastifyReply } from 'fastify';
import { parseIfMatch, toEtag } from '../../../shared/http/etag.ts';
import type { Todo, TodoChanges, TodoDraft, TodoStatus } from '../domain/todo.ts';
import type { TodoSort } from '../application/ports/todo.repository.ts';
import type { TodoUseCases } from '../todo.module.ts';
import {
  changeStatusSchema,
  createTodoSchema,
  deleteTodoSchema,
  getTodoSchema,
  listTodosSchema,
  updateTodoSchema,
  type TodoSortParam,
} from './todo.schemas.ts';

export interface TodoRoutesOptions {
  useCases: TodoUseCases;
}

interface IdParams {
  id: string;
}

interface IfMatchHeaders {
  'if-match'?: string;
}

interface ListQuerystring {
  status?: TodoStatus;
  q?: string;
  sort: TodoSortParam;
  limit: number;
  offset: number;
}

type WriteRequest = { Params: IdParams; Headers: IfMatchHeaders };

export const todoRoutes: FastifyPluginCallback<TodoRoutesOptions> = (app, { useCases }, done) => {
  app.post<{ Body: TodoDraft }>('/', { schema: createTodoSchema }, async (request, reply) => {
    const todo = await useCases.create.execute(request.body);
    return sendTodo(reply.status(201).header('location', `${app.prefix}/${todo.id}`), todo);
  });

  app.get<{ Querystring: ListQuerystring }>('/', { schema: listTodosSchema }, (request) => {
    const { status, q, sort, limit, offset } = request.query;
    return useCases.list.execute({ status, search: q, sort: parseSort(sort), limit, offset });
  });

  app.get<{ Params: IdParams }>('/:id', { schema: getTodoSchema }, async (request, reply) => {
    return sendTodo(reply, await useCases.get.execute(request.params.id));
  });

  app.patch<WriteRequest & { Body: TodoChanges }>('/:id', { schema: updateTodoSchema }, async (request, reply) => {
    const todo = await useCases.update.execute({
      id: request.params.id,
      expectedVersion: parseIfMatch(request.headers['if-match']),
      changes: request.body,
    });
    return sendTodo(reply, todo);
  });

  app.post<WriteRequest>('/:id/complete', { schema: changeStatusSchema }, async (request, reply) => {
    const expectedVersion = parseIfMatch(request.headers['if-match']);
    return sendTodo(reply, await useCases.complete.execute(request.params.id, expectedVersion));
  });

  app.post<WriteRequest>('/:id/reopen', { schema: changeStatusSchema }, async (request, reply) => {
    const expectedVersion = parseIfMatch(request.headers['if-match']);
    return sendTodo(reply, await useCases.reopen.execute(request.params.id, expectedVersion));
  });

  app.delete<WriteRequest>('/:id', { schema: deleteTodoSchema }, async (request, reply) => {
    await useCases.remove.execute(request.params.id, parseIfMatch(request.headers['if-match']));
    return reply.status(204).send();
  });

  done();
};

function sendTodo(reply: FastifyReply, todo: Todo): FastifyReply {
  return reply.header('etag', toEtag(todo.version)).send(todo);
}

function parseSort(param: TodoSortParam): TodoSort {
  const descending = param.startsWith('-');
  const field = (descending ? param.slice(1) : param) as TodoSort['field'];
  return { field, direction: descending ? 'desc' : 'asc' };
}

import { errorResponseSchema } from '../../../shared/http/error-response.ts';
import { TODO_PRIORITIES, TODO_STATUSES } from '../domain/todo.ts';

export const TODO_SORT_PARAMS = ['createdAt', '-createdAt', 'dueDate', '-dueDate'] as const;
export type TodoSortParam = (typeof TODO_SORT_PARAMS)[number];

const title = { type: 'string', minLength: 1, maxLength: 200 } as const;
const description = { type: ['string', 'null'], maxLength: 5000 } as const;
const dueDate = { type: ['string', 'null'], format: 'date' } as const;
const priority = { type: ['string', 'null'], enum: [...TODO_PRIORITIES, null] } as const;

const todoResponse = {
  type: 'object',
  required: ['id', 'title', 'description', 'dueDate', 'priority', 'status', 'completedAt', 'version', 'createdAt', 'updatedAt'],
  properties: {
    id: { type: 'string', format: 'uuid' },
    title: { type: 'string' },
    description: { type: ['string', 'null'] },
    dueDate: { type: ['string', 'null'] },
    priority: { type: ['string', 'null'] },
    status: { type: 'string' },
    completedAt: { type: ['string', 'null'] },
    version: { type: 'integer' },
    createdAt: { type: 'string' },
    updatedAt: { type: 'string' },
  },
} as const;

const idParams = {
  type: 'object',
  required: ['id'],
  properties: { id: { type: 'string', format: 'uuid' } },
} as const;

const ifMatchHeaders = {
  type: 'object',
  properties: { 'if-match': { type: 'string' } },
} as const;

const writeErrors = {
  400: errorResponseSchema,
  404: errorResponseSchema,
  412: errorResponseSchema,
  428: errorResponseSchema,
} as const;

export const createTodoSchema = {
  body: {
    type: 'object',
    required: ['title'],
    additionalProperties: false,
    properties: { title, description, dueDate, priority },
  },
  response: { 201: todoResponse, 400: errorResponseSchema },
} as const;

export const listTodosSchema = {
  querystring: {
    type: 'object',
    properties: {
      status: { type: 'string', enum: TODO_STATUSES },
      q: { type: 'string', minLength: 1, maxLength: 100 },
      sort: { type: 'string', enum: TODO_SORT_PARAMS, default: '-createdAt' },
      limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
      offset: { type: 'integer', minimum: 0, maximum: 10_000, default: 0 },
    },
  },
  response: {
    200: {
      type: 'object',
      required: ['items', 'total', 'limit', 'offset'],
      properties: {
        items: { type: 'array', items: todoResponse },
        total: { type: 'integer' },
        limit: { type: 'integer' },
        offset: { type: 'integer' },
      },
    },
    400: errorResponseSchema,
  },
} as const;

export const getTodoSchema = {
  params: idParams,
  response: { 200: todoResponse, 400: errorResponseSchema, 404: errorResponseSchema },
} as const;

export const updateTodoSchema = {
  params: idParams,
  headers: ifMatchHeaders,
  body: {
    type: 'object',
    minProperties: 1,
    additionalProperties: false,
    properties: { title, description, dueDate, priority },
  },
  response: { 200: todoResponse, ...writeErrors },
} as const;

export const changeStatusSchema = {
  params: idParams,
  headers: ifMatchHeaders,
  response: { 200: todoResponse, ...writeErrors },
} as const;

export const deleteTodoSchema = {
  params: idParams,
  headers: ifMatchHeaders,
  response: { 204: { type: 'null' }, ...writeErrors },
} as const;

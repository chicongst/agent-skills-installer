import { STATUS_CODES } from 'node:http';
import type { FastifyError, FastifyReply, FastifyRequest } from 'fastify';
import { AppError, type ErrorKind } from '../errors/app-error.ts';
import { errorBody } from './error-response.ts';

const STATUS_BY_KIND: Readonly<Record<ErrorKind, number>> = {
  validation: 400,
  not_found: 404,
  conflict: 409,
  version_mismatch: 412,
  precondition_required: 428,
};

export function errorHandler(error: FastifyError, request: FastifyRequest, reply: FastifyReply): FastifyReply {
  if (error instanceof AppError) {
    request.log.info({ err: error }, 'request rejected');
    return reply
      .status(STATUS_BY_KIND[error.kind])
      .send(errorBody(request, error.code, error.message, error.details));
  }

  if (error.validation) {
    return reply
      .status(400)
      .send(errorBody(request, 'VALIDATION_FAILED', error.message, { issues: error.validation }));
  }

  const status = error.statusCode;
  if (status !== undefined && status >= 400 && status < 500) {
    return reply.status(status).send(errorBody(request, statusName(status), error.message));
  }

  request.log.error({ err: error }, 'unhandled error');
  return reply.status(500).send(errorBody(request, 'INTERNAL_ERROR', 'Internal server error'));
}

export function notFoundHandler(request: FastifyRequest, reply: FastifyReply): FastifyReply {
  return reply
    .status(404)
    .send(errorBody(request, 'ROUTE_NOT_FOUND', `Route ${request.method} ${request.url} not found`));
}

function statusName(status: number): string {
  return (STATUS_CODES[status] ?? 'Bad Request').toUpperCase().replace(/\W+/g, '_');
}

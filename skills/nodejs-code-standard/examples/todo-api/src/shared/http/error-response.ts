import type { FastifyRequest } from 'fastify';

export interface ErrorBody {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    requestId: string;
  };
}

export const errorResponseSchema = {
  type: 'object',
  required: ['error'],
  properties: {
    error: {
      type: 'object',
      required: ['code', 'message', 'requestId'],
      properties: {
        code: { type: 'string' },
        message: { type: 'string' },
        details: { type: 'object', additionalProperties: true },
        requestId: { type: 'string' },
      },
    },
  },
} as const;

export function errorBody(
  request: FastifyRequest,
  code: string,
  message: string,
  details?: Record<string, unknown>,
): ErrorBody {
  return { error: { code, message, ...(details && { details }), requestId: request.id } };
}

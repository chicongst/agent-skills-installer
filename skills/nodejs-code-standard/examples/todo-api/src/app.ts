import Fastify, { type FastifyInstance } from 'fastify';
import type { Config } from './config/env.ts';
import type { Container } from './container.ts';
import { errorHandler, notFoundHandler } from './shared/http/error-handler.ts';
import { validatorCompiler } from './shared/http/validator-compiler.ts';
import { todoRoutes } from './modules/todos/http/todo.routes.ts';

export interface BuildAppOptions {
  config: Pick<Config, 'logLevel'>;
  container: Container;
}

export async function buildApp({ config, container }: BuildAppOptions): Promise<FastifyInstance> {
  const app = Fastify({
    logger: {
      level: config.logLevel,
      redact: ['req.headers.authorization', 'req.headers.cookie'],
    },
    requestIdHeader: 'x-request-id',
    bodyLimit: 1_048_576,
  });

  app.setValidatorCompiler(validatorCompiler);
  app.setErrorHandler(errorHandler);
  app.setNotFoundHandler(notFoundHandler);

  app.get('/health', () => ({ status: 'ok' }));
  await app.register(todoRoutes, { prefix: '/todos', useCases: container.todos });

  return app;
}

import type { FastifyInstance } from 'fastify';
import { buildApp } from '../../src/app.ts';
import { loadConfig } from '../../src/config/env.ts';
import { createContainer, type ContainerOverrides } from '../../src/container.ts';

export async function buildTestApp(overrides: ContainerOverrides = {}): Promise<FastifyInstance> {
  const config = loadConfig({ NODE_ENV: 'test', LOG_LEVEL: 'silent', STORAGE_DRIVER: 'memory' });
  const container = createContainer(config, overrides);
  const app = await buildApp({ config, container });
  app.addHook('onClose', () => container.close());
  return app;
}

import { buildApp } from './app.ts';
import { loadConfig } from './config/env.ts';
import { createContainer } from './container.ts';
import { registerProcessHandlers } from './shared/lifecycle/process-handlers.ts';

const config = loadConfig();
const container = createContainer(config);
const app = await buildApp({ config, container });

registerProcessHandlers({
  logger: app.log,
  shutdownTimeoutMs: config.shutdownTimeoutMs,
  closers: [() => app.close(), () => container.close()],
});

await app.listen({ host: config.host, port: config.port });

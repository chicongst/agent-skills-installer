import type { FastifyBaseLogger } from 'fastify';

export type Closer = () => Promise<void>;

export interface ProcessHandlerOptions {
  logger: FastifyBaseLogger;
  shutdownTimeoutMs: number;
  closers: readonly Closer[];
}

export function registerProcessHandlers({ logger, shutdownTimeoutMs, closers }: ProcessHandlerOptions): void {
  let shuttingDown = false;

  async function shutdown(signal: NodeJS.Signals): Promise<void> {
    if (shuttingDown) return;
    shuttingDown = true;
    logger.info({ signal }, 'shutting down');

    const timer = setTimeout(() => {
      logger.error({ shutdownTimeoutMs }, 'shutdown timed out, forcing exit');
      process.exit(1);
    }, shutdownTimeoutMs);
    timer.unref();

    try {
      for (const close of closers) await close();
      process.exit(0);
    } catch (err) {
      logger.error({ err }, 'error during shutdown');
      process.exit(1);
    }
  }

  for (const signal of ['SIGINT', 'SIGTERM'] as const) {
    process.once(signal, (received) => void shutdown(received));
  }

  process.on('unhandledRejection', (reason) => {
    logger.fatal({ err: reason }, 'unhandled rejection');
    process.exit(1);
  });

  process.on('uncaughtException', (err) => {
    logger.fatal({ err }, 'uncaught exception');
    process.exit(1);
  });
}

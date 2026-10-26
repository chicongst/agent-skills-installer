const NODE_ENVS = ['development', 'test', 'production'] as const;
const LOG_LEVELS = ['fatal', 'error', 'warn', 'info', 'debug', 'trace', 'silent'] as const;
const STORAGE_DRIVERS = ['memory', 'postgres'] as const;

export type NodeEnv = (typeof NODE_ENVS)[number];
export type LogLevel = (typeof LOG_LEVELS)[number];

export type StorageConfig =
  | { readonly driver: 'memory' }
  | { readonly driver: 'postgres'; readonly databaseUrl: string };

export interface Config {
  readonly nodeEnv: NodeEnv;
  readonly host: string;
  readonly port: number;
  readonly logLevel: LogLevel;
  readonly shutdownTimeoutMs: number;
  readonly storage: StorageConfig;
}

export class ConfigError extends Error {
  override name = 'ConfigError';
}

export function loadConfig(env: NodeJS.ProcessEnv = process.env): Config {
  return Object.freeze({
    nodeEnv: oneOf('NODE_ENV', env.NODE_ENV ?? 'development', NODE_ENVS),
    host: env.HOST ?? '127.0.0.1',
    port: integer('PORT', env.PORT ?? '3000', 0, 65_535),
    logLevel: oneOf('LOG_LEVEL', env.LOG_LEVEL ?? 'info', LOG_LEVELS),
    shutdownTimeoutMs: integer('SHUTDOWN_TIMEOUT_MS', env.SHUTDOWN_TIMEOUT_MS ?? '10000', 1_000, 120_000),
    storage: storage(env),
  });
}

function storage(env: NodeJS.ProcessEnv): StorageConfig {
  const driver = oneOf('STORAGE_DRIVER', env.STORAGE_DRIVER ?? 'memory', STORAGE_DRIVERS);
  if (driver === 'memory') return { driver };

  const databaseUrl = env.DATABASE_URL;
  if (!databaseUrl) throw new ConfigError('DATABASE_URL is required when STORAGE_DRIVER=postgres');
  return { driver, databaseUrl };
}

function oneOf<T extends string>(key: string, value: string, allowed: readonly T[]): T {
  if (!(allowed as readonly string[]).includes(value)) {
    throw new ConfigError(`${key} must be one of ${allowed.join(', ')}, got "${value}"`);
  }
  return value as T;
}

function integer(key: string, value: string, min: number, max: number): number {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < min || parsed > max) {
    throw new ConfigError(`${key} must be an integer between ${String(min)} and ${String(max)}, got "${value}"`);
  }
  return parsed;
}

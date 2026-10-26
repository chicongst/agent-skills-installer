import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { ConfigError, loadConfig } from '../../src/config/env.ts';

describe('loadConfig', () => {
  it('defaults to in-memory storage', () => {
    assert.deepEqual(loadConfig({}).storage, { driver: 'memory' });
  });

  it('requires DATABASE_URL for postgres', () => {
    assert.throws(() => loadConfig({ STORAGE_DRIVER: 'postgres' }), ConfigError);
  });

  it('fails fast on an invalid port', () => {
    assert.throws(() => loadConfig({ PORT: 'abc' }), ConfigError);
  });
});

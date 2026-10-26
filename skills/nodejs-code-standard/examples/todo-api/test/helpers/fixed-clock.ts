import type { Clock } from '../../src/shared/time/clock.ts';

export interface FixedClock extends Clock {
  advance(ms: number): void;
}

export function fixedClock(startIso = '2026-01-01T09:00:00.000Z'): FixedClock {
  let current = new Date(startIso).getTime();
  return {
    now: () => new Date(current),
    advance: (ms) => {
      current += ms;
    },
  };
}

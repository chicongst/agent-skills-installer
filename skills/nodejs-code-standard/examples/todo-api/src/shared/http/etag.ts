import { PreconditionRequiredError, ValidationError } from '../errors/app-error.ts';

export function toEtag(version: number): string {
  return `"${String(version)}"`;
}

export function parseIfMatch(header: string | undefined): number {
  if (header === undefined) {
    throw new PreconditionRequiredError('If-Match header with the current ETag is required');
  }
  const match = /^"(\d+)"$/.exec(header.trim());
  if (!match?.[1]) {
    throw new ValidationError('If-Match must be a strong ETag such as "3"', {
      details: { header: 'if-match' },
    });
  }
  return Number(match[1]);
}

export type ErrorKind =
  | 'validation'
  | 'not_found'
  | 'conflict'
  | 'version_mismatch'
  | 'precondition_required';

export interface AppErrorOptions {
  cause?: unknown;
  details?: Record<string, unknown>;
}

export abstract class AppError extends Error {
  abstract readonly kind: ErrorKind;
  abstract readonly code: string;
  readonly details: Record<string, unknown> | undefined;

  constructor(message: string, options: AppErrorOptions = {}) {
    super(message, { cause: options.cause });
    this.name = new.target.name;
    this.details = options.details;
  }
}

export class ValidationError extends AppError {
  readonly kind = 'validation';
  readonly code = 'VALIDATION_FAILED';
}

export class NotFoundError extends AppError {
  readonly kind = 'not_found';
  readonly code = 'NOT_FOUND';
}

export class ConflictError extends AppError {
  readonly kind = 'conflict';
  readonly code = 'CONFLICT';
}

export class VersionMismatchError extends AppError {
  readonly kind = 'version_mismatch';
  readonly code = 'VERSION_MISMATCH';
}

export class PreconditionRequiredError extends AppError {
  readonly kind = 'precondition_required';
  readonly code = 'PRECONDITION_REQUIRED';
}

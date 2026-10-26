import { NotFoundError, VersionMismatchError } from '../../../shared/errors/app-error.ts';

export class TodoNotFoundError extends NotFoundError {
  constructor(id: string) {
    super(`Todo ${id} not found`, { details: { id } });
  }
}

export class TodoVersionMismatchError extends VersionMismatchError {
  constructor(currentVersion: number) {
    super('Todo was modified by someone else; reload and retry', { details: { currentVersion } });
  }
}

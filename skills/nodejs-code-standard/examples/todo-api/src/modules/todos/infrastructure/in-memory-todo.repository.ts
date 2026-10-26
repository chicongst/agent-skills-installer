import type { Page } from '../../../shared/pagination/page.ts';
import type { Todo } from '../domain/todo.ts';
import type {
  TodoListQuery,
  TodoRepository,
  TodoSort,
  WriteResult,
} from '../application/ports/todo.repository.ts';

export class InMemoryTodoRepository implements TodoRepository {
  readonly #rows = new Map<string, Todo>();

  findById(id: string): Promise<Todo | undefined> {
    const row = this.#rows.get(id);
    return Promise.resolve(row && structuredClone(row));
  }

  list(query: TodoListQuery): Promise<Page<Todo>> {
    const search = query.search?.toLowerCase();
    const matches = [...this.#rows.values()]
      .filter((todo) => query.status === undefined || todo.status === query.status)
      .filter((todo) => search === undefined || todo.title.toLowerCase().includes(search))
      .sort(compareBy(query.sort));

    return Promise.resolve({
      items: matches.slice(query.offset, query.offset + query.limit).map((todo) => structuredClone(todo)),
      total: matches.length,
      limit: query.limit,
      offset: query.offset,
    });
  }

  insert(todo: Todo): Promise<void> {
    this.#rows.set(todo.id, structuredClone(todo));
    return Promise.resolve();
  }

  update(todo: Todo, expectedVersion: number): Promise<WriteResult> {
    const result = this.#check(todo.id, expectedVersion);
    if (result === 'written') this.#rows.set(todo.id, structuredClone(todo));
    return Promise.resolve(result);
  }

  delete(id: string, expectedVersion: number): Promise<WriteResult> {
    const result = this.#check(id, expectedVersion);
    if (result === 'written') this.#rows.delete(id);
    return Promise.resolve(result);
  }

  #check(id: string, expectedVersion: number): WriteResult {
    const current = this.#rows.get(id);
    if (!current) return 'not_found';
    return current.version === expectedVersion ? 'written' : 'version_mismatch';
  }
}

function compareBy({ field, direction }: TodoSort): (a: Todo, b: Todo) => number {
  const sign = direction === 'asc' ? 1 : -1;
  return (a, b) => {
    const left = a[field];
    const right = b[field];
    if (left === right) return a.id.localeCompare(b.id);
    if (left === null) return 1;
    if (right === null) return -1;
    return left < right ? -sign : sign;
  };
}

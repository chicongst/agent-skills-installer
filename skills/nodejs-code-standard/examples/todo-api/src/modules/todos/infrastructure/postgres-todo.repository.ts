import type { Pool } from 'pg';
import type { Page } from '../../../shared/pagination/page.ts';
import type { Todo, TodoPriority, TodoStatus } from '../domain/todo.ts';
import type {
  TodoListQuery,
  TodoRepository,
  TodoSortField,
  WriteResult,
} from '../application/ports/todo.repository.ts';

interface TodoRow {
  id: string;
  title: string;
  description: string | null;
  due_date: string | null;
  priority: TodoPriority | null;
  status: TodoStatus;
  completed_at: Date | null;
  version: number;
  created_at: Date;
  updated_at: Date;
}

const SELECT_COLUMNS = `id, title, description, to_char(due_date, 'YYYY-MM-DD') AS due_date,
  priority, status, completed_at, version, created_at, updated_at`;

const SORT_COLUMNS: Readonly<Record<TodoSortField, string>> = {
  createdAt: 'created_at',
  dueDate: 'due_date',
};

export class PostgresTodoRepository implements TodoRepository {
  readonly #pool: Pool;

  constructor(pool: Pool) {
    this.#pool = pool;
  }

  async findById(id: string): Promise<Todo | undefined> {
    const { rows } = await this.#pool.query<TodoRow>(`SELECT ${SELECT_COLUMNS} FROM todos WHERE id = $1`, [id]);
    const [row] = rows;
    return row ? toTodo(row) : undefined;
  }

  async list(query: TodoListQuery): Promise<Page<Todo>> {
    const params: unknown[] = [];
    const bind = (value: unknown): string => {
      params.push(value);
      return `$${String(params.length)}`;
    };

    const filters: string[] = [];
    if (query.status !== undefined) filters.push(`status = ${bind(query.status)}`);
    if (query.search !== undefined) filters.push(`title ILIKE ${bind(`%${escapeLike(query.search)}%`)} ESCAPE '\\'`);
    const where = filters.length > 0 ? `WHERE ${filters.join(' AND ')}` : '';
    const filterParams = [...params];

    const direction = query.sort.direction === 'asc' ? 'ASC' : 'DESC';
    const orderBy = `ORDER BY ${SORT_COLUMNS[query.sort.field]} ${direction} NULLS LAST, id ASC`;
    const page = `LIMIT ${bind(query.limit)} OFFSET ${bind(query.offset)}`;

    const [items, count] = await Promise.all([
      this.#pool.query<TodoRow>(`SELECT ${SELECT_COLUMNS} FROM todos ${where} ${orderBy} ${page}`, params),
      this.#pool.query<{ total: string }>(`SELECT count(*) AS total FROM todos ${where}`, filterParams),
    ]);

    return {
      items: items.rows.map(toTodo),
      total: Number(count.rows[0]?.total ?? 0),
      limit: query.limit,
      offset: query.offset,
    };
  }

  async insert(todo: Todo): Promise<void> {
    await this.#pool.query(
      `INSERT INTO todos
         (id, title, description, due_date, priority, status, completed_at, version, created_at, updated_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
      [
        todo.id,
        todo.title,
        todo.description,
        todo.dueDate,
        todo.priority,
        todo.status,
        todo.completedAt,
        todo.version,
        todo.createdAt,
        todo.updatedAt,
      ],
    );
  }

  async update(todo: Todo, expectedVersion: number): Promise<WriteResult> {
    const { rowCount } = await this.#pool.query(
      `UPDATE todos
          SET title = $3, description = $4, due_date = $5, priority = $6, status = $7,
              completed_at = $8, version = $9, updated_at = $10
        WHERE id = $1 AND version = $2`,
      [
        todo.id,
        expectedVersion,
        todo.title,
        todo.description,
        todo.dueDate,
        todo.priority,
        todo.status,
        todo.completedAt,
        todo.version,
        todo.updatedAt,
      ],
    );
    return rowCount === 1 ? 'written' : this.#missReason(todo.id);
  }

  async delete(id: string, expectedVersion: number): Promise<WriteResult> {
    const { rowCount } = await this.#pool.query('DELETE FROM todos WHERE id = $1 AND version = $2', [
      id,
      expectedVersion,
    ]);
    return rowCount === 1 ? 'written' : this.#missReason(id);
  }

  async #missReason(id: string): Promise<WriteResult> {
    const { rowCount } = await this.#pool.query('SELECT 1 FROM todos WHERE id = $1', [id]);
    return rowCount === 0 ? 'not_found' : 'version_mismatch';
  }
}

function toTodo(row: TodoRow): Todo {
  return {
    id: row.id,
    title: row.title,
    description: row.description,
    dueDate: row.due_date,
    priority: row.priority,
    status: row.status,
    completedAt: row.completed_at?.toISOString() ?? null,
    version: row.version,
    createdAt: row.created_at.toISOString(),
    updatedAt: row.updated_at.toISOString(),
  };
}

function escapeLike(value: string): string {
  return value.replace(/[\\%_]/g, '\\$&');
}

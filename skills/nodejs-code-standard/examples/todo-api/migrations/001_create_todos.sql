CREATE TABLE todos (
  id           uuid        PRIMARY KEY,
  title        text        NOT NULL CHECK (char_length(title) BETWEEN 1 AND 200),
  description  text        CHECK (char_length(description) <= 5000),
  due_date     date,
  priority     text        CHECK (priority IN ('low', 'medium', 'high')),
  status       text        NOT NULL CHECK (status IN ('open', 'done')),
  completed_at timestamptz,
  version      integer     NOT NULL CHECK (version >= 1),
  created_at   timestamptz NOT NULL,
  updated_at   timestamptz NOT NULL
);

CREATE INDEX todos_status_created_at_idx ON todos (status, created_at DESC, id);
CREATE INDEX todos_due_date_idx ON todos (due_date NULLS LAST, id);

PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS books (
 id INTEGER PRIMARY KEY, title TEXT NOT NULL, author TEXT NOT NULL,
 category TEXT NOT NULL, publisher TEXT NOT NULL DEFAULT '',
 year INTEGER NOT NULL CHECK(year BETWEEN 1000 AND 2100), isbn TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS copies (
 id INTEGER PRIMARY KEY, book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE RESTRICT,
 code TEXT NOT NULL UNIQUE, shelf TEXT NOT NULL,
 condition TEXT NOT NULL DEFAULT 'available' CHECK(condition IN ('available','damaged','lost'))
);
CREATE TABLE IF NOT EXISTS readers (
 id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
 email TEXT NOT NULL DEFAULT '', phone TEXT NOT NULL DEFAULT '',
 expires TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1))
);
CREATE TABLE IF NOT EXISTS loans (
 id INTEGER PRIMARY KEY, reader_id INTEGER NOT NULL REFERENCES readers(id) ON DELETE RESTRICT,
 copy_id INTEGER NOT NULL REFERENCES copies(id) ON DELETE RESTRICT,
 borrowed TEXT NOT NULL, due TEXT NOT NULL, returned TEXT,
 renewals INTEGER NOT NULL DEFAULT 0 CHECK(renewals BETWEEN 0 AND 1),
 return_condition TEXT CHECK(return_condition IN ('available','damaged','lost')),
 CHECK(due >= borrowed), CHECK(returned IS NULL OR returned >= borrowed),
 CHECK((returned IS NULL AND return_condition IS NULL) OR (returned IS NOT NULL AND return_condition IS NOT NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS one_open_loan_per_copy ON loans(copy_id) WHERE returned IS NULL;
CREATE INDEX IF NOT EXISTS loans_reader ON loans(reader_id);

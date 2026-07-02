// Pure CSV-to-contacts parser. No filesystem, no process, no console — see R10.
// parseCsv(content) takes the full CSV text and returns { contacts, errors }.
// A malformed/missing header is fatal and is signaled by throwing HeaderError;
// per-row problems are non-fatal and collected into `errors` instead.

const REQUIRED_COLUMNS = ['name', 'email', 'phone'];

// Minimum bar for "syntactically valid": non-empty local part, an '@', a
// domain with at least one dot, and no whitespace anywhere.
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export class HeaderError extends Error {
  constructor(message) {
    super(message);
    this.name = 'HeaderError';
  }
}

// R1: the header must be EXACTLY the set {name,email,phone} (any order).
// Missing, unexpected, and duplicated columns are all fatal; every problem
// that applies is named in the thrown HeaderError's message.
function validateHeader(headerFields) {
  const problems = [];

  const missing = REQUIRED_COLUMNS.filter((col) => !headerFields.includes(col));
  if (missing.length > 0) {
    problems.push(`missing required column(s): ${missing.join(', ')}`);
  }

  const unexpected = [...new Set(headerFields.filter((f) => !REQUIRED_COLUMNS.includes(f)))];
  if (unexpected.length > 0) {
    problems.push(`unexpected column(s): ${unexpected.join(', ')}`);
  }

  const duplicated = [...new Set(headerFields.filter((f, idx) => headerFields.indexOf(f) !== idx))];
  if (duplicated.length > 0) {
    problems.push(`duplicate column(s): ${duplicated.join(', ')}`);
  }

  if (problems.length > 0) {
    throw new HeaderError(problems.join('; '));
  }
}

function stripBom(text) {
  return text.charCodeAt(0) === 0xfeff ? text.slice(1) : text;
}

// Tokenizes raw CSV text into rows of { fields: string[], line: number }.
// `line` is the 1-based line number in the original text where the row
// begins (the header is line 1). Handles quoted fields containing commas,
// escaped quotes (""), embedded newlines, and both CRLF and LF endings.
function tokenizeRows(text) {
  const rows = [];
  const n = text.length;
  let i = 0;
  let line = 1;
  let rowStartLine = line;
  let field = '';
  let row = [];
  let inQuotes = false;
  let atFieldStart = true;

  const endField = () => {
    row.push(field);
    field = '';
    atFieldStart = true;
  };
  const endRow = () => {
    endField();
    rows.push({ fields: row, line: rowStartLine });
    row = [];
  };

  while (i < n) {
    const ch = text[i];

    if (inQuotes) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i += 2;
        } else {
          inQuotes = false;
          i += 1;
        }
      } else if (ch === '\r' && text[i + 1] === '\n') {
        field += '\n';
        line += 1;
        i += 2;
      } else if (ch === '\n') {
        field += '\n';
        line += 1;
        i += 1;
      } else {
        field += ch;
        i += 1;
      }
      continue;
    }

    if (atFieldStart && ch === '"') {
      inQuotes = true;
      atFieldStart = false;
      i += 1;
      continue;
    }

    if (ch === ',') {
      endField();
      i += 1;
      continue;
    }

    if (ch === '\r' && text[i + 1] === '\n') {
      endRow();
      line += 1;
      i += 2;
      rowStartLine = line;
      continue;
    }

    if (ch === '\n') {
      endRow();
      line += 1;
      i += 1;
      rowStartLine = line;
      continue;
    }

    field += ch;
    atFieldStart = false;
    i += 1;
  }

  // Only flush a trailing row if there's actually unterminated content —
  // a file ending in a newline must not produce a phantom empty row.
  if (field.length > 0 || row.length > 0) {
    endRow();
  }

  return rows;
}

function normalizePhone(raw) {
  return raw.replace(/[\s\-()]/g, '');
}

// string in -> { contacts, errors } out. Throws HeaderError for a missing
// or absent header (fatal); per-row problems are pushed onto `errors`
// instead of aborting the run.
export function parseCsv(content) {
  const text = stripBom(content);
  const rows = tokenizeRows(text);

  if (rows.length === 0) {
    throw new HeaderError(`missing required column(s): ${REQUIRED_COLUMNS.join(', ')}`);
  }

  const headerFields = rows[0].fields.map((f) => f.trim());
  validateHeader(headerFields);

  const colIndex = {
    name: headerFields.indexOf('name'),
    email: headerFields.indexOf('email'),
    phone: headerFields.indexOf('phone'),
  };
  const expectedFieldCount = headerFields.length;

  const contacts = [];
  const errors = [];
  const seenEmails = new Set();

  for (const { fields, line } of rows.slice(1)) {
    if (fields.length !== expectedFieldCount) {
      errors.push({
        line,
        reason: `wrong field count (expected ${expectedFieldCount}, got ${fields.length})`,
      });
      continue;
    }

    const name = fields[colIndex.name].trim();
    if (name.length === 0) {
      errors.push({ line, reason: 'empty name' });
      continue;
    }

    const email = fields[colIndex.email].trim();
    if (!EMAIL_RE.test(email)) {
      errors.push({ line, reason: 'invalid email' });
      continue;
    }

    const emailKey = email.toLowerCase();
    if (seenEmails.has(emailKey)) {
      errors.push({ line, reason: 'duplicate email' });
      continue;
    }

    const phone = normalizePhone(fields[colIndex.phone].trim());
    if (!/^\d+$/.test(phone)) {
      errors.push({ line, reason: 'invalid phone' });
      continue;
    }

    seenEmails.add(emailKey);
    contacts.push({ name, email, phone });
  }

  return { contacts, errors };
}

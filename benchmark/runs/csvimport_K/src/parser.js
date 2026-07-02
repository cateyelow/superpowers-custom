// Pure CSV contact parsing/normalization logic.
// String in -> { contacts, errors } out. No filesystem access, no process.exit.

const REQUIRED_COLUMNS = ['name', 'email', 'phone'];

// Pragmatic syntactic check: non-empty local part, '@', domain with a dot,
// and no whitespace or extra '@' anywhere.
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** Thrown when the header row is missing or is not exactly {name,email,phone}. */
export class HeaderError extends Error {
  constructor(message, { missing = [], unexpected = [] } = {}) {
    super(message);
    this.name = 'HeaderError';
    this.missing = missing;
    this.unexpected = unexpected;
  }
}

function stripBom(text) {
  return text.charCodeAt(0) === 0xfeff ? text.slice(1) : text;
}

/**
 * Tokenize CSV text into records (RFC 4180 style: quoted fields may contain
 * commas, escaped quotes `""`, and newlines). Handles LF, CRLF, and lone CR
 * line endings. Blank lines are skipped.
 *
 * Returns [{ fields: string[], line: number }] where `line` is the 1-based
 * physical line number in the original text at which the record starts.
 */
function tokenize(text) {
  const records = [];
  let fields = [];
  let field = '';
  let inQuotes = false;
  let line = 1;
  let recordLine = 1;
  let recordStarted = false;

  const endField = () => {
    fields.push(field);
    field = '';
  };
  const endRecord = () => {
    endField();
    const isBlankLine = fields.length === 1 && fields[0].trim() === '';
    if (!isBlankLine) records.push({ fields, line: recordLine });
    fields = [];
    recordStarted = false;
  };

  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (!recordStarted) {
      recordLine = line;
      recordStarted = true;
    }
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        if (c === '\n') line++;
        field += c;
      }
    } else if (c === '"') {
      inQuotes = true;
    } else if (c === ',') {
      endField();
    } else if (c === '\r') {
      if (text[i + 1] !== '\n') {
        // Lone CR acts as a line ending; CRLF is handled by the '\n' branch.
        line++;
        endRecord();
      }
    } else if (c === '\n') {
      line++;
      endRecord();
    } else {
      field += c;
    }
  }
  if (recordStarted) endRecord();
  return records;
}

function validateHeader(headerFields) {
  const normalized = headerFields.map((f) => f.trim().toLowerCase());
  const seen = new Set();
  const unexpected = [];
  for (const col of normalized) {
    if (!REQUIRED_COLUMNS.includes(col) || seen.has(col)) unexpected.push(col);
    seen.add(col);
  }
  const missing = REQUIRED_COLUMNS.filter((c) => !seen.has(c));
  if (missing.length > 0 || unexpected.length > 0) {
    const parts = [];
    if (missing.length > 0) parts.push(`missing required column(s): ${missing.join(', ')}`);
    if (unexpected.length > 0) parts.push(`unexpected column(s): ${unexpected.join(', ')}`);
    throw new HeaderError(`invalid header: ${parts.join('; ')}`, { missing, unexpected });
  }
  return {
    name: normalized.indexOf('name'),
    email: normalized.indexOf('email'),
    phone: normalized.indexOf('phone'),
  };
}

// Strip spaces, dashes, and parentheses; the result must be digits only.
function normalizePhone(raw) {
  const digits = raw.replace(/[\s\-()]/g, '');
  return /^\d+$/.test(digits) ? digits : null;
}

/**
 * Parse a contacts CSV (header: name,email,phone in any order).
 *
 * @param {string} csvText - Full CSV file contents (BOM/CRLF tolerated).
 * @returns {{ contacts: Array<{name: string, email: string, phone: string}>,
 *             errors: Array<{line: number, reason: string}> }}
 *   `errors[].line` is the 1-based line number in the original file
 *   (the header is line 1).
 * @throws {HeaderError} if the header is missing or not exactly {name,email,phone}.
 */
export function parseContacts(csvText) {
  const records = tokenize(stripBom(String(csvText)));
  if (records.length === 0) {
    throw new HeaderError(
      `invalid header: missing required column(s): ${REQUIRED_COLUMNS.join(', ')}`,
      { missing: [...REQUIRED_COLUMNS] },
    );
  }

  const columnIndex = validateHeader(records[0].fields);
  const contacts = [];
  const errors = [];
  const seenEmails = new Set();

  for (const { fields, line } of records.slice(1)) {
    if (fields.length !== REQUIRED_COLUMNS.length) {
      errors.push({
        line,
        reason: `expected ${REQUIRED_COLUMNS.length} fields, got ${fields.length}`,
      });
      continue;
    }

    const name = fields[columnIndex.name].trim();
    const email = fields[columnIndex.email].trim();
    const phone = normalizePhone(fields[columnIndex.phone].trim());

    let reason = null;
    if (name === '') reason = 'empty name';
    else if (!EMAIL_RE.test(email)) reason = 'invalid email';
    else if (phone === null) reason = 'invalid phone';
    else if (seenEmails.has(email.toLowerCase())) reason = 'duplicate email';

    if (reason !== null) {
      errors.push({ line, reason });
      continue;
    }

    seenEmails.add(email.toLowerCase());
    contacts.push({ name, email, phone });
  }

  return { contacts, errors };
}

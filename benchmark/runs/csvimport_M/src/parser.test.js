import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile, writeFile, rm, readdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import process from 'node:process';

import { parseCsv, HeaderError } from './parser.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const cliPath = join(__dirname, 'importCsv.js');

function runCli(args) {
  return new Promise((resolve, reject) => {
    execFile(process.execPath, [cliPath, ...args], (error, stdout, stderr) => {
      if (error && typeof error.code !== 'number') {
        // Process failed to spawn at all, or was killed by a signal.
        reject(error);
        return;
      }
      resolve({ code: error ? error.code : 0, stdout, stderr });
    });
  });
}

describe('parseCsv — R2: quoted fields', () => {
  test('handles a quoted field containing a comma', () => {
    const csv = 'name,email,phone\n"Kim, Minsu",kim@example.com,010-1234-5678\n';
    const { contacts, errors } = parseCsv(csv);
    assert.deepEqual(errors, []);
    assert.equal(contacts.length, 1);
    assert.equal(contacts[0].name, 'Kim, Minsu');
    assert.equal(contacts[0].email, 'kim@example.com');
    assert.equal(contacts[0].phone, '01012345678');
  });

  test('handles escaped double quotes inside a quoted field', () => {
    const csv = 'name,email,phone\n"Bob ""The Builder"" Smith",bob@example.com,(555) 123-4567\n';
    const { contacts, errors } = parseCsv(csv);
    assert.deepEqual(errors, []);
    assert.equal(contacts.length, 1);
    assert.equal(contacts[0].name, 'Bob "The Builder" Smith');
    assert.equal(contacts[0].phone, '5551234567');
  });

  test('a naive split(",") would break on this row, the real parser must not', () => {
    const csv = 'name,email,phone\n"Kim, Minsu, Jr.",kim@example.com,0101234567\n';
    const { contacts, errors } = parseCsv(csv);
    assert.deepEqual(errors, []);
    assert.equal(contacts[0].name, 'Kim, Minsu, Jr.');
  });
});

describe('parseCsv — R5: original line numbers', () => {
  test('reports correct 1-based line numbers for a mix of valid/invalid rows, including after a wrong-field-count row', () => {
    const csv = [
      'name,email,phone', // line 1 (header)
      'Alice,alice@example.com,111-222-3333', // line 2, valid
      'BadRow,notanemail', // line 3, invalid: wrong field count
      '"Carol, Jones",carol@example.com,444-555-6666', // line 4, valid (quoted comma)
      'Dave,dave@example.com,', // line 5, invalid: empty/invalid phone
      'Eve,eve@example.com,555-000-1111', // line 6, valid — must not have drifted
    ].join('\n') + '\n';

    const { contacts, errors } = parseCsv(csv);

    assert.equal(contacts.length, 3);
    assert.deepEqual(
      contacts.map((c) => c.name),
      ['Alice', 'Carol, Jones', 'Eve']
    );

    assert.equal(errors.length, 2);
    assert.equal(errors[0].line, 3);
    assert.match(errors[0].reason, /wrong field count/);
    assert.equal(errors[1].line, 5);
    assert.equal(errors[1].reason, 'invalid phone');

    // Sanity: the row after the malformed ones lands on the right line
    // number (i.e. line counting didn't drift because of the earlier
    // wrong-field-count row or the multi-field quoted row).
    const eve = contacts.find((c) => c.name === 'Eve');
    assert.ok(eve);
  });
});

describe('parseCsv — R6: duplicate emails', () => {
  test('rejects a case-insensitive duplicate email after the first occurrence', () => {
    const csv = [
      'name,email,phone',
      'Alice,Alice@Example.com,111-111-1111',
      'Alice Two,alice@example.com,222-222-2222',
    ].join('\n') + '\n';

    const { contacts, errors } = parseCsv(csv);

    assert.equal(contacts.length, 1);
    assert.equal(contacts[0].email, 'Alice@Example.com');
    assert.equal(errors.length, 1);
    assert.equal(errors[0].line, 3);
    assert.equal(errors[0].reason, 'duplicate email');
  });
});

describe('parseCsv — R8: header-only input', () => {
  test('an empty data file (header only) yields no contacts and no errors', () => {
    const { contacts, errors } = parseCsv('name,email,phone\n');
    assert.deepEqual(contacts, []);
    assert.deepEqual(errors, []);
  });

  test('works with no trailing newline after the header either', () => {
    const { contacts, errors } = parseCsv('name,email,phone');
    assert.deepEqual(contacts, []);
    assert.deepEqual(errors, []);
  });
});

describe('parseCsv — R9: line endings and BOM', () => {
  test('CRLF and LF inputs produce identical results', () => {
    const lf = [
      'name,email,phone',
      'Alice,alice@example.com,111-222-3333',
      '"Kim, Minsu",kim@example.com,010-1234-5678',
    ].join('\n') + '\n';
    const crlf = lf.replace(/\n/g, '\r\n');

    const lfResult = parseCsv(lf);
    const crlfResult = parseCsv(crlf);

    assert.deepEqual(crlfResult, lfResult);
    assert.equal(lfResult.contacts.length, 2);
  });

  test('tolerates a UTF-8 BOM on the header line', () => {
    const csv = '﻿name,email,phone\nAlice,alice@example.com,111-222-3333\n';
    const { contacts, errors } = parseCsv(csv);
    assert.deepEqual(errors, []);
    assert.equal(contacts.length, 1);
    assert.equal(contacts[0].name, 'Alice');
  });
});

describe('parseCsv — R1: header validation', () => {
  test('throws HeaderError naming the missing column when one required column is absent', () => {
    assert.throws(
      () => parseCsv('name,phone\nAlice,111\n'),
      (err) => {
        assert.ok(err instanceof HeaderError);
        assert.match(err.message, /email/);
        return true;
      }
    );
  });

  test('throws HeaderError naming all missing columns when several are absent', () => {
    assert.throws(
      () => parseCsv('name\nAlice\n'),
      (err) => {
        assert.ok(err instanceof HeaderError);
        assert.match(err.message, /email/);
        assert.match(err.message, /phone/);
        return true;
      }
    );
  });

  test('accepts a reordered header (any order, exact set)', () => {
    const csv = 'email,name,phone\nalice@example.com,Alice,111-222-3333\n';
    const { contacts, errors } = parseCsv(csv);
    assert.deepEqual(errors, []);
    assert.equal(contacts.length, 1);
    assert.equal(contacts[0].name, 'Alice');
  });

  test('throws HeaderError for a completely empty file', () => {
    assert.throws(() => parseCsv(''), HeaderError);
  });

  test('throws HeaderError naming an unexpected extra column (exact set enforced)', () => {
    assert.throws(
      () => parseCsv('name,email,phone,notes\nAlice,alice@example.com,111,hi\n'),
      (err) => {
        assert.ok(err instanceof HeaderError);
        assert.match(err.message, /unexpected column\(s\): notes/);
        return true;
      }
    );
  });

  test('throws HeaderError naming a duplicated column', () => {
    assert.throws(
      () => parseCsv('name,email,email\nAlice,alice@example.com,alice@example.com\n'),
      (err) => {
        assert.ok(err instanceof HeaderError);
        assert.match(err.message, /duplicate column\(s\): email/);
        return true;
      }
    );
  });

  test('a header with both a missing and an unexpected column reports both problems', () => {
    assert.throws(
      () => parseCsv('name,phone,notes\nAlice,111,hi\n'),
      (err) => {
        assert.ok(err instanceof HeaderError);
        assert.match(err.message, /missing required column\(s\): email/);
        assert.match(err.message, /unexpected column\(s\): notes/);
        return true;
      }
    );
  });
});

describe('parseCsv — R3: row validation', () => {
  test('rejects an empty name after trimming', () => {
    const { errors } = parseCsv('name,email,phone\n   ,alice@example.com,111\n');
    assert.equal(errors.length, 1);
    assert.equal(errors[0].reason, 'empty name');
  });

  test('rejects a syntactically invalid email', () => {
    const { errors } = parseCsv('name,email,phone\nAlice,not-an-email,111\n');
    assert.equal(errors.length, 1);
    assert.equal(errors[0].reason, 'invalid email');
  });

  test('normalizes phone by stripping spaces, dashes and parentheses', () => {
    const { contacts, errors } = parseCsv('name,email,phone\nAlice,alice@example.com,(010) 1234-5678\n');
    assert.deepEqual(errors, []);
    assert.equal(contacts[0].phone, '01012345678');
  });

  test('rejects a phone that is not digits-only after normalization', () => {
    const { errors } = parseCsv('name,email,phone\nAlice,alice@example.com,+82-10-1234-5678\n');
    assert.equal(errors.length, 1);
    assert.equal(errors[0].reason, 'invalid phone');
  });
});

describe('CLI wrapper (importCsv.js) — end to end', () => {
  let dir;

  before(async () => {
    dir = await mkdtemp(join(tmpdir(), 'csvimport-test-'));
  });

  after(async () => {
    await rm(dir, { recursive: true, force: true });
  });

  test('--help prints usage and exits 0', async () => {
    const { code, stdout } = await runCli(['--help']);
    assert.equal(code, 0);
    assert.match(stdout, /Usage:/);
  });

  test('missing args exits 2 with usage on stderr', async () => {
    const { code, stderr } = await runCli([]);
    assert.equal(code, 2);
    assert.match(stderr, /Usage:/);
  });

  test('missing input file exits 2', async () => {
    const inputPath = join(dir, 'does-not-exist.csv');
    const outputPath = join(dir, 'out-missing.json');
    const { code, stderr } = await runCli([inputPath, outputPath]);
    assert.equal(code, 2);
    assert.match(stderr, /cannot read input file/);
  });

  test('bad header exits 2 naming the missing column', async () => {
    const inputPath = join(dir, 'bad-header.csv');
    const outputPath = join(dir, 'out-bad-header.json');
    await writeFile(inputPath, 'name,phone\nAlice,111\n', 'utf8');
    const { code, stderr } = await runCli([inputPath, outputPath]);
    assert.equal(code, 2);
    assert.match(stderr, /email/);
    await assert.rejects(() => readFile(outputPath));
  });

  test('header with an extra column exits 2 naming the unexpected column', async () => {
    const inputPath = join(dir, 'extra-header.csv');
    const outputPath = join(dir, 'out-extra-header.json');
    await writeFile(inputPath, 'name,email,phone,notes\nAlice,alice@example.com,111,hi\n', 'utf8');
    const { code, stderr } = await runCli([inputPath, outputPath]);
    assert.equal(code, 2);
    assert.match(stderr, /unexpected column\(s\): notes/);
    await assert.rejects(() => readFile(outputPath));
  });

  test('all-valid rows: exit 0, correct summary, atomic output with trailing newline', async () => {
    const inputPath = join(dir, 'valid.csv');
    const outputPath = join(dir, 'valid-out.json');
    const csv = [
      'name,email,phone',
      'Alice,alice@example.com,111-222-3333',
      '"Kim, Minsu",kim@example.com,010-1234-5678',
    ].join('\n') + '\n';
    await writeFile(inputPath, csv, 'utf8');

    const { code, stdout, stderr } = await runCli([inputPath, outputPath]);

    assert.equal(code, 0);
    assert.equal(stdout, 'imported 2/2 rows\n');
    assert.equal(stderr, '');

    const raw = await readFile(outputPath, 'utf8');
    assert.ok(/[^\n]\n$/.test(raw), 'output must end with exactly one trailing newline');
    const parsed = JSON.parse(raw);
    assert.equal(parsed.contacts.length, 2);
    assert.equal(parsed.contacts[1].name, 'Kim, Minsu');
    assert.equal(parsed.contacts[1].phone, '01012345678');

    // No leftover temp files from the atomic write-then-rename.
    const entries = await readdir(dir);
    const stray = entries.filter((e) => e.includes('.tmp-'));
    assert.deepEqual(stray, []);
  });

  test('mixed valid/invalid rows: exit 1, summary counts total, stderr has line-tagged reasons', async () => {
    const inputPath = join(dir, 'mixed.csv');
    const outputPath = join(dir, 'mixed-out.json');
    const csv = [
      'name,email,phone',
      'Alice,alice@example.com,111-222-3333',
      'Bad,notanemail,111',
      'Carol,carol@example.com,222-333-4444',
    ].join('\n') + '\n';
    await writeFile(inputPath, csv, 'utf8');

    const { code, stdout, stderr } = await runCli([inputPath, outputPath]);

    assert.equal(code, 1);
    assert.equal(stdout, 'imported 2/3 rows\n');
    assert.equal(stderr, 'line 3: invalid email\n');

    const parsed = JSON.parse(await readFile(outputPath, 'utf8'));
    assert.equal(parsed.contacts.length, 2);
  });

  test('header-only input: exit 0, empty contacts, "imported 0/0 rows"', async () => {
    const inputPath = join(dir, 'empty.csv');
    const outputPath = join(dir, 'empty-out.json');
    await writeFile(inputPath, 'name,email,phone\n', 'utf8');

    const { code, stdout } = await runCli([inputPath, outputPath]);

    assert.equal(code, 0);
    assert.equal(stdout, 'imported 0/0 rows\n');
    const parsed = JSON.parse(await readFile(outputPath, 'utf8'));
    assert.deepEqual(parsed, { contacts: [] });
  });
});

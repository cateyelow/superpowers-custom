import { describe, test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { parseContacts, HeaderError } from './parser.js';

describe('parseContacts: happy path', () => {
  test('parses valid rows into normalized contacts', () => {
    const csv = 'name,email,phone\nKim Minsu,kim@example.com,010-1234-5678\n';
    const { contacts, errors } = parseContacts(csv);
    assert.deepEqual(errors, []);
    assert.deepEqual(contacts, [
      { name: 'Kim Minsu', email: 'kim@example.com', phone: '01012345678' },
    ]);
  });

  test('header columns may appear in any order', () => {
    const csv = 'phone,name,email\n(02) 555-0100,Lee,lee@example.com\n';
    const { contacts, errors } = parseContacts(csv);
    assert.deepEqual(errors, []);
    assert.deepEqual(contacts, [
      { name: 'Lee', email: 'lee@example.com', phone: '025550100' },
    ]);
  });

  test('phone is normalized to digits only (spaces, dashes, parentheses stripped)', () => {
    const csv = 'name,email,phone\nA,a@b.co,(010) 1234-5678\n';
    const { contacts } = parseContacts(csv);
    assert.equal(contacts[0].phone, '01012345678');
  });
});

describe('R2: quoting', () => {
  test('quoted field containing a comma is one field', () => {
    const csv = 'name,email,phone\n"Kim, Minsu",kim@example.com,01012345678\n';
    const { contacts, errors } = parseContacts(csv);
    assert.deepEqual(errors, []);
    assert.equal(contacts.length, 1);
    assert.equal(contacts[0].name, 'Kim, Minsu');
  });

  test('escaped quotes ("") inside a quoted field become a literal quote', () => {
    const csv = 'name,email,phone\n"Kim ""Minsu"" Jr.",kim@example.com,01012345678\n';
    const { contacts, errors } = parseContacts(csv);
    assert.deepEqual(errors, []);
    assert.equal(contacts[0].name, 'Kim "Minsu" Jr.');
  });

  test('quoted field may contain a newline; later line numbers stay correct', () => {
    const csv =
      'name,email,phone\n' + // line 1
      '"Multi\nLine",multi@example.com,111\n' + // lines 2-3
      'Bad,not-an-email,222\n'; // line 4
    const { contacts, errors } = parseContacts(csv);
    assert.equal(contacts.length, 1);
    assert.equal(contacts[0].name, 'Multi\nLine');
    assert.deepEqual(errors, [{ line: 4, reason: 'invalid email' }]);
  });
});

describe('R1: header validation', () => {
  test('missing column throws HeaderError naming it', () => {
    const csv = 'name,email\nKim,kim@example.com\n';
    assert.throws(
      () => parseContacts(csv),
      (err) => {
        assert.ok(err instanceof HeaderError);
        assert.deepEqual(err.missing, ['phone']);
        assert.match(err.message, /phone/);
        return true;
      },
    );
  });

  test('multiple missing columns are all named', () => {
    assert.throws(
      () => parseContacts('name\nKim\n'),
      (err) => {
        assert.ok(err instanceof HeaderError);
        assert.deepEqual(err.missing.sort(), ['email', 'phone']);
        assert.match(err.message, /email/);
        assert.match(err.message, /phone/);
        return true;
      },
    );
  });

  test('empty input throws HeaderError', () => {
    assert.throws(() => parseContacts(''), HeaderError);
  });

  test('unexpected extra column throws HeaderError (exact set required)', () => {
    assert.throws(() => parseContacts('name,email,phone,age\n'), HeaderError);
  });
});

describe('R3: row validation', () => {
  test('invalid email is rejected', () => {
    const csv = 'name,email,phone\nKim,not-an-email,01012345678\n';
    const { contacts, errors } = parseContacts(csv);
    assert.deepEqual(contacts, []);
    assert.deepEqual(errors, [{ line: 2, reason: 'invalid email' }]);
  });

  test('name empty after trimming is rejected', () => {
    const csv = 'name,email,phone\n   ,kim@example.com,01012345678\n';
    const { errors } = parseContacts(csv);
    assert.deepEqual(errors, [{ line: 2, reason: 'empty name' }]);
  });

  test('phone with non-digit garbage is rejected', () => {
    const csv = 'name,email,phone\nKim,kim@example.com,call-me\n';
    const { errors } = parseContacts(csv);
    assert.deepEqual(errors, [{ line: 2, reason: 'invalid phone' }]);
  });

  test('row with wrong field count is rejected, not fatal', () => {
    const csv = 'name,email,phone\nKim,kim@example.com\nLee,lee@example.com,02555\n';
    const { contacts, errors } = parseContacts(csv);
    assert.equal(contacts.length, 1);
    assert.equal(errors.length, 1);
    assert.equal(errors[0].line, 2);
    assert.match(errors[0].reason, /field/);
  });
});

describe('R5: invalid rows are collected with original 1-based line numbers', () => {
  test('mix of valid and invalid rows: run continues, line numbers correct', () => {
    const csv = [
      'name,email,phone', // line 1 (header)
      'Kim,kim@example.com,010-1111-2222', // line 2 valid
      'NoEmail,broken,0311112222', // line 3 invalid email
      'Lee,lee@example.com,031 111 2222', // line 4 valid
      ',park@example.com,0211112222', // line 5 empty name
      'Choi,choi@example.com,02-111-2222', // line 6 valid
    ].join('\n') + '\n';
    const { contacts, errors } = parseContacts(csv);
    assert.deepEqual(contacts.map((c) => c.name), ['Kim', 'Lee', 'Choi']);
    assert.deepEqual(errors, [
      { line: 3, reason: 'invalid email' },
      { line: 5, reason: 'empty name' },
    ]);
  });
});

describe('R6: duplicate emails (case-insensitive)', () => {
  test('second occurrence is rejected with reason "duplicate email"', () => {
    const csv = [
      'name,email,phone',
      'Kim,kim@example.com,0101',
      'Kim2,KIM@EXAMPLE.COM,0102',
      'Lee,lee@example.com,0103',
    ].join('\n') + '\n';
    const { contacts, errors } = parseContacts(csv);
    assert.deepEqual(contacts.map((c) => c.email), ['kim@example.com', 'lee@example.com']);
    assert.deepEqual(errors, [{ line: 3, reason: 'duplicate email' }]);
  });

  test('a rejected row does not reserve its email for duplicate detection', () => {
    const csv = [
      'name,email,phone',
      ',kim@example.com,0101', // invalid (empty name) - must not claim the email
      'Kim,kim@example.com,0102', // first VALID occurrence -> imported
    ].join('\n') + '\n';
    const { contacts, errors } = parseContacts(csv);
    assert.deepEqual(contacts.map((c) => c.name), ['Kim']);
    assert.deepEqual(errors, [{ line: 2, reason: 'empty name' }]);
  });
});

describe('R8: header-only file', () => {
  test('yields empty contacts and no errors', () => {
    const { contacts, errors } = parseContacts('name,email,phone\n');
    assert.deepEqual(contacts, []);
    assert.deepEqual(errors, []);
  });

  test('header without trailing newline also works', () => {
    const { contacts, errors } = parseContacts('name,email,phone');
    assert.deepEqual(contacts, []);
    assert.deepEqual(errors, []);
  });
});

describe('R9: line endings and BOM', () => {
  test('CRLF line endings parse identically to LF', () => {
    const csv = 'name,email,phone\r\nKim,kim@example.com,0101\r\nBad,broken,0102\r\n';
    const { contacts, errors } = parseContacts(csv);
    assert.deepEqual(contacts, [{ name: 'Kim', email: 'kim@example.com', phone: '0101' }]);
    assert.deepEqual(errors, [{ line: 3, reason: 'invalid email' }]);
  });

  test('UTF-8 BOM on the header line is tolerated', () => {
    const csv = '﻿name,email,phone\nKim,kim@example.com,0101\n';
    const { contacts, errors } = parseContacts(csv);
    assert.deepEqual(errors, []);
    assert.equal(contacts[0].name, 'Kim');
  });

  test('BOM + CRLF together', () => {
    const csv = '﻿name,email,phone\r\nKim,kim@example.com,0101\r\n';
    const { contacts, errors } = parseContacts(csv);
    assert.deepEqual(errors, []);
    assert.equal(contacts.length, 1);
  });
});

describe('R10: parser purity', () => {
  test('returns data instead of exiting, even for all-invalid input', () => {
    const { contacts, errors } = parseContacts('name,email,phone\nx,broken,y\n');
    assert.deepEqual(contacts, []);
    assert.equal(errors.length, 1);
  });
});

// ---------------------------------------------------------------------------
// CLI wrapper (importCsv.js): exit codes, summary, atomic write, --help
// ---------------------------------------------------------------------------

describe('CLI: importCsv.js', () => {
  const cliPath = fileURLToPath(new URL('./importCsv.js', import.meta.url));
  let dir;

  before(() => {
    dir = mkdtempSync(join(tmpdir(), 'csvimport-test-'));
  });
  after(() => {
    rmSync(dir, { recursive: true, force: true });
  });

  function runCli(...args) {
    return spawnSync(process.execPath, [cliPath, ...args], { encoding: 'utf8' });
  }

  test('R7: all rows valid -> exit 0, summary on stdout, JSON with trailing newline', () => {
    const input = join(dir, 'ok.csv');
    const output = join(dir, 'ok.json');
    writeFileSync(input, 'name,email,phone\nKim,kim@example.com,010-1234-5678\n');
    const res = runCli(input, output);
    assert.equal(res.status, 0);
    assert.equal(res.stdout, 'imported 1/1 rows\n');
    const raw = readFileSync(output, 'utf8');
    assert.ok(raw.endsWith('\n'), 'output must end with a trailing newline');
    assert.deepEqual(JSON.parse(raw), {
      contacts: [{ name: 'Kim', email: 'kim@example.com', phone: '01012345678' }],
    });
  });

  test('R7/R5: some rows rejected -> exit 1, errors on stderr as "line <n>: <reason>"', () => {
    const input = join(dir, 'mixed.csv');
    const output = join(dir, 'mixed.json');
    writeFileSync(
      input,
      'name,email,phone\nKim,kim@example.com,0101\nBad,broken,0102\n',
    );
    const res = runCli(input, output);
    assert.equal(res.status, 1);
    assert.equal(res.stdout, 'imported 1/2 rows\n');
    assert.match(res.stderr, /^line 3: invalid email$/m);
    assert.deepEqual(JSON.parse(readFileSync(output, 'utf8')).contacts.length, 1);
  });

  test('R8: header-only input -> {contacts: []}, "imported 0/0 rows", exit 0', () => {
    const input = join(dir, 'empty.csv');
    const output = join(dir, 'empty.json');
    writeFileSync(input, 'name,email,phone\n');
    const res = runCli(input, output);
    assert.equal(res.status, 0);
    assert.equal(res.stdout, 'imported 0/0 rows\n');
    assert.deepEqual(JSON.parse(readFileSync(output, 'utf8')), { contacts: [] });
  });

  test('R1: bad header -> exit 2, stderr names the missing column, no output file', () => {
    const input = join(dir, 'badheader.csv');
    const output = join(dir, 'badheader.json');
    writeFileSync(input, 'name,email\nKim,kim@example.com\n');
    const res = runCli(input, output);
    assert.equal(res.status, 2);
    assert.match(res.stderr, /phone/);
    assert.equal(res.stdout, '');
    assert.throws(() => readFileSync(output));
  });

  test('R7: unreadable input -> exit 2', () => {
    const res = runCli(join(dir, 'no-such-file.csv'), join(dir, 'out.json'));
    assert.equal(res.status, 2);
    assert.notEqual(res.stderr, '');
  });

  test('R7: unwritable output -> exit 2', () => {
    const input = join(dir, 'w.csv');
    writeFileSync(input, 'name,email,phone\nKim,kim@example.com,0101\n');
    const res = runCli(input, join(dir, 'no-such-dir', 'out.json'));
    assert.equal(res.status, 2);
    assert.notEqual(res.stderr, '');
  });

  test('R4: atomic write leaves no temp files behind and replaces prior content', () => {
    const sub = join(dir, 'atomic');
    mkdirSync(sub);
    const input = join(sub, 'in.csv');
    const output = join(sub, 'out.json');
    writeFileSync(input, 'name,email,phone\nKim,kim@example.com,0101\n');
    writeFileSync(output, 'PREVIOUS CONTENT');
    const res = runCli(input, output);
    assert.equal(res.status, 0);
    assert.deepEqual(readdirSync(sub).sort(), ['in.csv', 'out.json']);
    assert.equal(
      JSON.parse(readFileSync(output, 'utf8')).contacts[0].email,
      'kim@example.com',
    );
  });

  test('R12: --help prints usage and exits 0', () => {
    const res = runCli('--help');
    assert.equal(res.status, 0);
    assert.match(res.stdout, /[Uu]sage/);
  });

  test('missing arguments -> usage on stderr, exit 2', () => {
    const res = runCli();
    assert.equal(res.status, 2);
    assert.match(res.stderr, /[Uu]sage/);
  });
});

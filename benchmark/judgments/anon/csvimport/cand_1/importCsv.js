#!/usr/bin/env node
// Thin CLI wrapper around parser.js: argv handling, file I/O, atomic write,
// error/summary reporting, and exit codes. All parsing logic lives in parser.js.

import { readFileSync, writeFileSync, renameSync, rmSync } from 'node:fs';
import { dirname, basename, join } from 'node:path';
import process from 'node:process';

import { parseContacts, HeaderError } from './parser.js';

const USAGE = `Usage: node src/importCsv.js <input.csv> <output.json>

Imports a contacts CSV (header: name,email,phone in any order) into a
normalized JSON file: { "contacts": [{ "name", "email", "phone" }] }.

Invalid rows are reported to stderr as "line <n>: <reason>" and skipped.
A one-line summary "imported <k>/<total> rows" is printed to stdout.

Options:
  -h, --help    Show this help and exit.

Exit codes:
  0  all rows imported
  1  completed, but some rows were rejected
  2  fatal error (unreadable input, bad header, unwritable output)`;

function writeFileAtomic(outputPath, data) {
  const tempPath = join(
    dirname(outputPath),
    `.${basename(outputPath)}.${process.pid}.${Date.now()}.tmp`,
  );
  try {
    writeFileSync(tempPath, data);
    renameSync(tempPath, outputPath);
  } catch (err) {
    rmSync(tempPath, { force: true });
    throw err;
  }
}

function main(argv) {
  const args = argv.slice(2);
  if (args.includes('--help') || args.includes('-h')) {
    console.log(USAGE);
    return 0;
  }
  if (args.length !== 2) {
    console.error(USAGE);
    return 2;
  }
  const [inputPath, outputPath] = args;

  let csvText;
  try {
    csvText = readFileSync(inputPath, 'utf8');
  } catch (err) {
    console.error(`error: cannot read ${inputPath}: ${err.message}`);
    return 2;
  }

  let contacts;
  let errors;
  try {
    ({ contacts, errors } = parseContacts(csvText));
  } catch (err) {
    if (err instanceof HeaderError) {
      console.error(`error: ${err.message}`);
      return 2;
    }
    throw err;
  }

  for (const { line, reason } of errors) {
    console.error(`line ${line}: ${reason}`);
  }

  const json = `${JSON.stringify({ contacts }, null, 2)}\n`;
  try {
    writeFileAtomic(outputPath, json);
  } catch (err) {
    console.error(`error: cannot write ${outputPath}: ${err.message}`);
    return 2;
  }

  const total = contacts.length + errors.length;
  console.log(`imported ${contacts.length}/${total} rows`);
  return errors.length > 0 ? 1 : 0;
}

process.exit(main(process.argv));

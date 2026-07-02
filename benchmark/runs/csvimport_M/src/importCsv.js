#!/usr/bin/env node
// Thin I/O shell around parser.js: argv handling, reading input, writing
// output atomically, and choosing the process exit code (R10 — all parsing
// logic itself lives in the pure parser module).

import { readFile, writeFile, rename, unlink } from 'node:fs/promises';
import { dirname, join, basename } from 'node:path';
import process from 'node:process';
import { parseCsv, HeaderError } from './parser.js';

const USAGE = `Usage: node src/importCsv.js <input.csv> <output.json>

Imports a contacts CSV (header: name,email,phone, any order) into a
normalized JSON file: { "contacts": [ { "name", "email", "phone" }, ... ] }.

Invalid rows are skipped and reported on stderr; the run still succeeds
unless the input is unreadable, the header is missing a required column,
or the output can't be written.

Options:
  -h, --help    Show this help message and exit
`;

async function writeAtomic(outputPath, data) {
  const dir = dirname(outputPath) || '.';
  const tempPath = join(dir, `.${basename(outputPath)}.tmp-${process.pid}-${Date.now()}`);
  try {
    await writeFile(tempPath, data, 'utf8');
    await rename(tempPath, outputPath);
  } catch (err) {
    await unlink(tempPath).catch(() => {});
    throw err;
  }
}

async function main(argv) {
  if (argv.includes('--help') || argv.includes('-h')) {
    process.stdout.write(USAGE);
    return 0;
  }

  if (argv.length !== 2) {
    process.stderr.write(USAGE);
    return 2;
  }

  const [inputPath, outputPath] = argv;

  let content;
  try {
    content = await readFile(inputPath, 'utf8');
  } catch (err) {
    process.stderr.write(`error: cannot read input file '${inputPath}': ${err.message}\n`);
    return 2;
  }

  let result;
  try {
    result = parseCsv(content);
  } catch (err) {
    if (err instanceof HeaderError) {
      process.stderr.write(`error: ${err.message}\n`);
      return 2;
    }
    throw err;
  }

  const { contacts, errors } = result;
  const total = contacts.length + errors.length;
  const outputJson = `${JSON.stringify({ contacts }, null, 2)}\n`;

  try {
    await writeAtomic(outputPath, outputJson);
  } catch (err) {
    process.stderr.write(`error: cannot write output file '${outputPath}': ${err.message}\n`);
    return 2;
  }

  for (const { line, reason } of errors) {
    process.stderr.write(`line ${line}: ${reason}\n`);
  }
  process.stdout.write(`imported ${contacts.length}/${total} rows\n`);

  return errors.length > 0 ? 1 : 0;
}

try {
  const exitCode = await main(process.argv.slice(2));
  process.exit(exitCode);
} catch (err) {
  process.stderr.write(`error: ${err.message}\n`);
  process.exit(2);
}

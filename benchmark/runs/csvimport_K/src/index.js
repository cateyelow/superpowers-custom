// Test-runner shim. On Node v22, `node --test src/` does not scan the
// directory for test files (v21+ glob semantics); it executes `src` itself as
// a single test entry, which Node resolves to this index.js. Importing the
// test suite here makes the required invocation `node --test src/` run every
// test, with failures propagating to the runner's exit code.
import './parser.test.js';

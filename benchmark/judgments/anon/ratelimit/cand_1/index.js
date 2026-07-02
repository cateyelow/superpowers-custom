// Entry shim so the mandated verification command `node --test src/` works
// on the installed Node (v22.19.0).
//
// Since Node 21 the test runner treats positional arguments as file paths /
// globs, NOT searchable directories: `node --test src/` spawns `node src`,
// which resolves via this index file (measured on this box: v20.20.0 searches
// the directory and passes; v22.19.0 and v24.18.0 fail with MODULE_NOT_FOUND
// without this file). Importing the test module registers the whole suite in
// that child, so pass/fail propagates to the runner's exit code exactly as if
// the file had been discovered directly. On Node 20 this file is ignored (it
// does not match the *.test.js discovery pattern).
//
// This is intentionally the only thing this file does.
import './rateLimiter.test.js';

# Hashline Guard

Hashline Guard provides line-level integrity for file editing operations in Jarvis. It assigns a short hash tag to every line of a file, enabling the system to verify that a line has not changed between reading and editing.

## How It Works

### Tagged Output

When a file is read through Hashline Guard, each line is displayed with a hash tag:

```
 1#Xk| def hello():
 2#mA|     print("Hello, world!")
 3#00|
 4#Yp| def goodbye():
 5#rZ|     print("Goodbye!")
```

The format is `{line_number}#{2-char tag}| {content}`. The 2-character tag is a base62-encoded xxhash64 digest of the line content.

### Edit Validation

Before any edit is applied, Hashline Guard:

1. Looks up the file in its LRU cache.
2. Re-reads the target line from disk to get the freshest content.
3. Compares the hash tag provided in the edit intent against the current hash.
4. If they match, the edit proceeds atomically.
5. If they mismatch, the edit is rejected with a clear error message.

### Automatic Recovery

When a hash mismatch occurs (e.g., because the file was modified between read and edit), the recovery system:

1. Re-reads the entire file from disk.
2. Searches within +/-5 lines of the original position for the intended line.
3. Uses fuzzy matching (SequenceMatcher, threshold 0.8) to find relocated lines.
4. Retries the edit with the corrected line number and hash.
5. Gives up after `max_retries` attempts.

### Atomic Writes

All edits are performed atomically:
- Content is written to a temporary file in the same directory.
- `os.replace()` swaps the temp file into place.
- File permissions and encoding are preserved.
- Batch edits are applied as a single atomic write.

### Audit Trail

Every read and edit operation is logged to `~/.cognithor/hashline_audit.jsonl` as an append-only JSONL file. Each entry includes a SHA-256 hash for chain integrity.

## Configuration

Add to `config.yaml` under the `hashline` key:

```yaml
hashline:
  enabled: true                    # Enable/disable the system
  hash_algorithm: xxhash64         # Hash algorithm (only xxhash64 supported)
  tag_length: 2                    # Length of the base62 tag (2-4)
  max_file_size_mb: 10             # Maximum file size to process
  max_line_length: 10000           # Maximum line length in characters
  stale_threshold_seconds: 300     # Cache staleness threshold
  max_retries: 3                   # Recovery retry attempts
  retry_delay_seconds: 0.5         # Delay between retries
  cache_max_files: 100             # LRU cache capacity
  binary_detection: true           # Reject binary files
  audit_enabled: true              # Enable audit logging
  excluded_patterns:               # Files to skip
    - "*.pyc"
    - "__pycache__/**"
    - ".git/**"
    - "*.lock"
    - "node_modules/**"
  protected_paths: []              # Paths requiring extra confirmation
```

## Troubleshooting

### Hash Mismatch Errors

If you see "Hash mismatch on line X", it means the file was modified between reading and editing. The recovery system will attempt to find the line at its new position. If recovery fails:

- Re-read the file to get fresh hash tags.
- Use the updated tags in your edit command.

### Binary File Errors

Hashline Guard rejects binary files by default. To process a file that is incorrectly detected as binary, set `binary_detection: false` in the config (not recommended).

### File Too Large

Files exceeding `max_file_size_mb` are rejected. Increase the limit in config or use `read_range` to read specific line ranges.

### Cache Staleness

If edits fail unexpectedly, the cache may be stale. Call `invalidate(path)` to clear the cache for a specific file, or reduce `stale_threshold_seconds`.

<!--
name: 'Tool Description: Grep'
description: Structural code search using AST patterns via ast-grep
version: 2.0.0
-->

Search code structurally using AST patterns (ast-grep).

- Use `$VAR` wildcards for single node matching, `$$$VAR` for multiple nodes
- Matches code structure regardless of whitespace or formatting
- Specify `lang` for ambiguous files (auto-detected from extension)
- Supported: rust, javascript, typescript, python, go, java, c, cpp, etc.

**Critical rule**: Patterns must be valid **standalone syntax** in the target language. A pattern that only exists inside a class body or impl block is NOT standalone and will fail.

**Working patterns by language**:
- **Rust**: `pub fn $NAME($$$ARGS) -> $RET { $$$BODY }`, `impl $TRAIT for $TYPE { $$$BODY }`, `struct $NAME { $$$FIELDS }`, `let $X = $EXPR;`
- **TypeScript/JS**: `function $NAME($$$ARGS) { $$$BODY }`, `class $NAME { $$$BODY }`, `const $NAME = ($$$ARGS) => $BODY`, `$OBJ.$METHOD($$$ARGS)`
- **Go**: `func $NAME($$$ARGS) $RET { $$$BODY }`, `type $NAME struct { $$$FIELDS }`
- **Call patterns** (all languages): `tokio::spawn($$$ARGS)`, `console.log($$$ARGS)`, `$OBJ.$METHOD($$$ARGS)`

**Common pitfalls**:
- `update($$$ARGS): void { $$$BODY }` FAILS — method definitions are not standalone TS syntax. Use `function update($$$ARGS): void { $$$BODY }` or search by call pattern.
- `fn $NAME($$$ARGS)` may not match Rust functions that have `pub`/`pub(crate)` visibility. Include the modifier: `pub fn $NAME($$$ARGS)`.
- For class methods, search the entire class (`class $NAME { $$$BODY }`) or use call patterns (`$OBJ.$METHOD($$$ARGS)`).

When to use vs Grep: use AST mode when you care about **code structure**, use Grep for **text/regex** (strings, comments, config values).

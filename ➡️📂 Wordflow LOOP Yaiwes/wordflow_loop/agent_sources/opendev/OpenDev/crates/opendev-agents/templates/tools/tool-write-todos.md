<!--
name: 'Tool Description: TodoWrite'
description: Create a todo list for complex tasks
version: 3.0.0
-->

Create a structured task list at the START of a complex task. This helps track progress, organize multi-step work, and demonstrates thoroughness to the user.

## When to use

- Complex multi-step tasks requiring 3 or more distinct steps
- User provides multiple tasks (numbered or comma-separated)
- After receiving new instructions that involve significant work
- When using plan mode, group plan steps into 4-8 high-level parent todos with sub-steps as children

## When NOT to use

- Single straightforward task that can be completed in fewer than 3 trivial steps
- Trivial tasks where tracking provides no organizational benefit
- Purely conversational or informational tasks

## Task fields

- **content**: A brief, actionable title in plain text, imperative form (e.g., "Implement authentication system"). NEVER use markdown formatting — no **bold**, *italic*, `backticks`, or any markup. Plain text only.
- **activeForm**: Present continuous form shown in the spinner when the task is in_progress (e.g., "Implementing authentication"). Plain text only. ALWAYS provide this field.
- **status**: All initial items should use 'pending' status
- **children**: An array of strings representing sub-steps for this todo. Use this to break down a complex step into actionable sub-tasks. Children are NOT shown in the user's UI but ARE included in the status output so you can track which sub-steps remain. Always use children when a parent task has 2 or more distinct sub-steps.

## Usage notes

- Write 4-8 parent todo items maximum. Hard limit: 10 parent items. Excess parent items beyond 10 will be silently truncated.
- **Group related sub-steps as `children`** instead of creating separate top-level items. When you receive a detailed plan, consolidate plan steps into logical groups. Each group becomes a parent todo, and its individual steps become children.
- REPLACES the entire todo list — call EXACTLY ONCE, never call it twice. Then use TaskUpdate to change status as you work
- Exactly ONE task should be in_progress at any time. Mark it in_progress BEFORE beginning work on it
- ONLY mark a task as completed when you have FULLY accomplished it — including all its children sub-steps. Never mark completed if tests are failing, implementation is partial, or errors are unresolved
- After completing a task, check TaskList for the next available task

## Example

BAD — too many flat todos (will be truncated, loses detail):
```json
{"todos": ["Add login endpoint", "Add token validation", "Add auth middleware", "Create user model", "Add migration", "Write login tests", "Write middleware tests", "Add rate limiting", "Add logging", "Write rate limit tests", "Add caching", "Write cache tests"]}
```

GOOD — hierarchical with children (all detail preserved):
```json
{"todos": [
  {"content": "Implement authentication system", "activeForm": "Implementing authentication", "children": ["Add login endpoint", "Add token validation", "Add auth middleware"]},
  {"content": "Set up data layer", "activeForm": "Setting up data layer", "children": ["Create user model", "Add database migration"]},
  {"content": "Add rate limiting and caching", "activeForm": "Adding rate limiting", "children": ["Add rate limiting middleware", "Add caching layer"]},
  {"content": "Add observability", "activeForm": "Adding logging", "children": ["Add structured logging"]},
  {"content": "Write comprehensive tests", "activeForm": "Writing tests", "children": ["Write auth tests", "Write rate limit tests", "Write cache tests"]}
]}
```

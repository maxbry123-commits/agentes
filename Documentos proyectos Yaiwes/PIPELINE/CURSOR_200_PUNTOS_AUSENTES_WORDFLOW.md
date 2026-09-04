# 200 puntos de programación estilo Cursor AUSENTES o no equivalentes en Wordflow

**Base de comparación:** mapa forense + arquitectura REAL (`run_code_path` + standards).  
**Criterio:** punto típico en flujo Cursor/agent-IDE/senior+Cursor que **no** está implementado como enforcement/runtime en nuestro Wordflow de programming (o solo DOCUMENTED).

Leyenda: AUSENTE = no en path; DEBIL = parcial/docs only.

---

## A. Workspace & context (1–25)
1. Index semántico tipo codebase chat con ranking de relevancia  
2. @file / @folder scope explícito por turno  
3. @codebase query con límites de tokens  
4. @docs / @web grounding opcional con citas  
5. @git diff como contexto de tarea  
6. @commit messages como contexto  
7. Rules por glob con prioridad  
8. Rules not-applied telemetry  
9. Project memory corta vs larga  
10. Sticky intent across turns  
11. Auto-attach open tabs  
12. Auto-attach active selection  
13. Ignore patterns (.cursorignore) enforced  
14. Binary/large file exclusion  
15. Secrets redaction in context  
16. Context budget meter  
17. Context pin/unpin files  
18. Multi-root workspace index  
19. Monorepo package boundary awareness  
20. Language server symbols in context  
21. Type error context from diagnostics  
22. Linter diagnostics as input  
23. Test failure logs as input  
24. Terminal last command output as input  
25. Debug breakpoint context  

## B. Planning (26–45)
26. Plan mode obligatorio antes de multi-file  
27. Plan artifact reviewed by human  
28. Plan step checkboxes  
29. Plan → task graph  
30. Estimate blast radius in plan  
31. Plan risk score  
32. Plan requires test strategy  
33. Plan requires rollback strategy  
34. Plan links to ADR  
35. Plan frozen hash  
36. Re-plan on requirement change  
37. Parallel vs serial step marking  
38. Human approval gate mid-plan  
39. Max steps per plan  
40. Plan diff against previous plan  
41. Definition of done in plan  
42. Non-goals section enforced  
43. Acceptance criteria machine-checked  
44. Dependency order of edits  
45. Dry-run plan without writes  

## C. Edit application (46–75)
46. Inline diff view per hunk  
47. Accept/reject hunk  
48. Accept file / reject file  
49. Multi-file transaction apply  
50. Atomic apply rollback  
51. Apply only staged AI hunks  
52. No apply without plan id  
53. Path allowlist for writes  
54. Path denylist (secrets, vendor)  
55. Max files per apply  
56. Max LOC delta per apply  
57. Max churn percent per file  
58. Protect main/master branch  
59. Require feature branch  
60. Block edit on dirty unrelated files  
61. Format-on-apply  
62. Organize imports on apply  
63. Code action auto-fix  
64. Rename symbol refactor (LSP)  
65. Extract method refactor  
66. Move file + update imports  
67. Safe delete with reference check  
68. Generate stub + TODO gate  
69. Snippet expansion controlled  
70. Template file from skeleton  
71. Partial apply with residual markers  
72. Conflict detect with local edits  
73. 3-way merge AI vs user vs base  
74. Undo AI apply stack  
75. Redo AI apply stack  

## D. Verification (76–100)
76. Run nearest test on save  
77. Run affected tests only (test impact)  
78. Coverage delta gate  
79. Typecheck gate  
80. Lint gate  
81. Format check gate  
82. Import cycle gate on apply  
83. Dead code gate  
84. Complexity delta gate  
85. Mutation test sample  
86. Snapshot test update policy  
87. Visual regression (UI)  
88. Contract test consumers  
89. Property-based tests hook  
90. Fuzz smoke optional  
91. Benchmark regression  
92. Memory leak smoke  
93. Race detector optional  
94. Integration test env spinup  
95. Ephemeral DB fixture  
96. HTTP mock server fixture  
97. Golden file review  
98. Flake quarantine  
99. Test timeout policy  
100. Fail-fast vs full suite policy  

## E. Git / PR (101–125)
101. Auto branch name from task  
102. Conventional commits  
103. Commit split by concern  
104. PR template fill  
105. PR description from diff  
106. PR linked to issue/task  
107. Required reviewers CODEOWNERS  
108. Label risk high/medium/low  
109. CI status required green  
110. Merge queue  
111. Squash policy  
112. Signed commits  
113. Commit GPG/SSH verify  
114. Protected paths CODEOWNERS  
115. Draft PR first  
116. Stacked PRs  
117. Cherry-pick assistant  
118. Rebase assistant  
119. Conflict resolution assistant gated  
120. Changelog fragment  
121. Version bump suggestion  
122. Release notes draft  
123. Tag creation policy  
124. Revert PR one-click policy  
125. Post-merge verify job  

## F. Agent authority & safety (126–150)
126. Tool permission prompts  
127. Network allowlist  
128. Shell command allowlist  
129. No sudo policy  
130. Sandbox FS for agent  
131. Read-only mode  
132. Ask mode vs Agent mode  
133. Yolo/auto-apply off by default  
134. Confirmation on destructive ops  
135. Rate limit tool calls  
136. Max agent turns  
137. Max tool failures then stop  
138. Prompt injection filters  
139. Untrusted instruction quarantine  
140. Model pin per project  
141. Temperature policy  
142. System prompt checksum  
143. Tool result size limit  
144. Exfiltrate path block  
145. PII redaction  
146. Audit log of tool calls  
147. Replay tool session  
148. Agent session export  
149. Multi-agent isolation  
150. Supervisor agent veto  

## G. Architecture & design (151–170)
151. Arch unit test (fitness functions)  
152. Layer rule tests  
153. Package dependency matrix  
154. No-new-cyclic-deps gate  
155. Port/adapter presence test  
156. Domain purity test  
157. ADR required for layer breach  
158. RFC template  
159. Design doc review gate  
160. API first OpenAPI  
161. Schema-first protobuf/JSON Schema  
162. Backward compat checker  
163. Feature flag scaffolding  
164. Strangler pattern checklist  
165. Data migration dry-run  
166. Expand/contract migration  
167. Shadow traffic hook  
168. Canary config stub  
169. SLO impact note  
170. Threat model checkbox  

## H. DX / Cursor product loops (171–200)
171. Composer multi-file oriented UI state  
172. Chat-to-apply continuity  
173. Checkpoint code timeline  
174. Restore checkpoint  
175. Image/mock UI to code  
176. Terminal agent mode  
177. Background agent jobs  
178. Bugbot-style review comments  
179. Inline AI chat on selection  
180. Docstring/gen tests from symbol  
181. Explain code panel  
182. Fix from diagnostics one-click  
183. Generate PR from chat  
184. Notion/Linear task sync  
185. MCP tool registry  
186. MCP allowlist  
187. Custom modes (review/refactor/test)  
188. Memories user-level vs project  
189. Privacy mode (no train/retain)  
190. Usage/cost dashboard per session  
191. Fast vs slow model routing  
192. Tab autocomplete accept metrics  
193. Next-edit suggestion  
194. Peek definition assisted  
195. Symbol search AI ranked  
196. Shared team rules sync  
197. Rules lint (invalid frontmatter)  
198. Extension conflict detection  
199. Workspace trust model  
200. Update channel / rule version pin  

---

## Nota de uso

- Esta lista **no** dice que Wordflow deba implementar los 200.
- Sirve para priorizar gaps vs Cursor-class DX/agent safety.
- Ya cubiertos de forma parcial/real en Wordflow (NO listar como ausentes puros): COPY-FIRST scanner, VerdictAuthority, llm DENY en code_path, smoke CI, WiringGraph básico, forensic contract schema, AGENTS.md/.cursor/rules mínimos.

## Prioridad sugerida (top 15 para Wordflow)
1. Path allowlist writes (53)  
2. Max files/LOC delta (55–56)  
3. Plan mode multi-file (26–27)  
4. Diff accept/reject model for apply agent (46–48)  
5. Affected tests (77)  
6. Typecheck/lint gates (79–80)  
7. Tool allowlist/shell deny (126–128)  
8. Context budget + secrets redaction (16,15)  
9. PR/SHA binding + CI green required (109)  
10. CODEOWNERS (107)  
11. Arch fitness tests (151–154)  
12. Prompt injection / untrusted docs (138–139)  
13. Run ledger / checkpoint (173–174, audit 146)  
14. Model pin + policy snapshot auto (140, PolicySnapshot)  
15. Git diff as context (5) + scope from diff  

import { describe, expect, test } from "bun:test"
import { Effect } from "effect"
import { CodeMode } from "../src/index.js"

const execute = (options: CodeMode.ExecuteOptions) => Effect.runPromise(CodeMode.execute(options))

describe("input bindings", () => {
  test("makes a binding visible and usable", async () => {
    const result = await execute({ code: "return input.x + 1", bindings: { input: { x: 1 } } })

    expect(result).toMatchObject({ ok: true, value: 2 })
  })

  test("rejects reassignment like a const binding", async () => {
    const result = await execute({ code: "input = 2", bindings: { input: 1 } })

    expect(result).toMatchObject({
      ok: false,
      error: { kind: "ExecutionFailure", message: expect.stringContaining("Cannot assign to constant 'input'") },
    })
  })

  test("allows property mutation on the sandbox copy", async () => {
    const input = { x: 1 }
    const result = await execute({ code: "input.x += 1; return input.x", bindings: { input } })

    expect(result).toMatchObject({ ok: true, value: 2 })
    expect(input.x).toBe(1)
  })

  test("rejects reserved binding names", async () => {
    const result = await execute({ code: "return null", bindings: { tools: 1 } })

    expect(result).toMatchObject({
      ok: false,
      error: { kind: "InvalidDataValue", message: "Binding name 'tools' is reserved by CodeMode." },
    })
  })

  test("rejects non-identifier binding names", async () => {
    const result = await execute({ code: "return null", bindings: { "not-valid": 1 } })

    expect(result).toMatchObject({
      ok: false,
      error: {
        kind: "InvalidDataValue",
        message: "Binding name 'not-valid' must be a valid JavaScript identifier.",
      },
    })
  })

  test("rejects invalid binding data", async () => {
    const cyclic: Record<string, CodeMode.DataValue> = {}
    cyclic.self = cyclic
    const result = await execute({ code: "return invalid", bindings: { invalid: cyclic } })

    expect(result).toMatchObject({
      ok: false,
      error: { kind: "InvalidDataValue", message: "Binding 'invalid' contains a circular value." },
    })
  })

  test("works through reusable runtimes", async () => {
    const runtime = CodeMode.make({ bindings: { input: { x: 1 } } })
    const result = await Effect.runPromise(runtime.execute("return input.x + 1"))

    expect(result).toMatchObject({ ok: true, value: 2 })
  })
})

# Workflow Development Guide

Complete guide for creating, testing, and deploying intelligent security workflows with the BaseWorkflow template system.

---

## Table of Contents

1. [Core Concept](#-core-concept)
2. [Creating a Workflow](#-creating-a-workflow)
3. [Testing Workflows](#-testing-workflows)
4. [BaseWorkflow API](#-baseworkflow-api)
5. [Workflow Examples](#-workflow-examples)
6. [Best Practices](#-best-practices)
7. [Development Workflow](#-development-workflow)
8. [Troubleshooting](#-troubleshooting)
9. [Checklist](#-checklist)

---

## 🎯 Core Concept

**BaseWorkflow** = Reusable template that automatically handles:
- ✅ Imports and dependencies
- ✅ JSON parsing (naabu, nuclei, etc.)
- ✅ Error handling
- ✅ Progress display
- ✅ Standardized result structure

**You = Just the tool commands!**

This system reduces workflow creation from **1 hour to 10 minutes**.

---

## 🚀 Creating a Workflow

### Step 1: Copy the Template

```bash
cd src/tools/workflows/
cp TEMPLATE.py my_workflow.py
```

### Step 2: Implement Your Workflow

```python
from src.tools.workflows.base import BaseWorkflow

class MyWorkflow(BaseWorkflow):

    def my_scan(self, target: str, timeout: int = 1200):
        steps = {}

        # Step 1: Port scanning
        success, findings, output = self.execute_step(
            step_name="Port scanning",
            command=f"naabu -host {target} -json",
            timeout=timeout // 2,
        )
        steps["ports"] = {
            "success": success,
            "ports": self.extract_ports(findings)
        }

        # Step 2: Vulnerability scan
        success, findings, output = self.execute_step(
            step_name="Vuln scan",
            command=f"nuclei -target {target} -json -silent",
            timeout=timeout // 2,
        )
        steps["vulns"] = {
            "success": success,
            "count": len(findings)
        }

        # Summary
        summary = {
            "total_ports": len(steps["ports"]["ports"]),
            "total_vulns": steps["vulns"]["count"]
        }

        return self.create_result_dict("my_scan", target, steps, summary)
```

### Step 3: Expose in server.py

```python
# In src/server.py

from src.tools.workflows.my_workflow import MyWorkflow

# Initialize
my_workflow = MyWorkflow(docker_client)

# Expose via MCP
@mcp.tool()
def my_scan(target: str, timeout: int = 1200) -> Dict[str, Any]:
    """Description of your workflow"""
    return my_workflow.my_scan(target, timeout)
```

**That's it! 🎉**

---

## 🧪 Testing Workflows

### Why Test?

- ✅ **Detect bugs** before exposing to LLM
- ✅ **Validate structure** of results
- ✅ **Check timeouts** and performance
- ✅ **Iterate quickly** during development

### Quick Testing Usage

#### 1. Validate Structure

Verify that your workflow inherits from BaseWorkflow and list available methods:

```bash
uv run python test_workflow.py --validate src/tools/workflows/my_workflow.py MyWorkflow
```

**Output:**
```
✓ Class 'MyWorkflow' loaded
✓ MyWorkflow inherits from BaseWorkflow
✓ Workflow methods available: 2
  • my_scan()
  • advanced_scan()
✅ Valid workflow file!
```

#### 2. Test Execution (Real Mode)

Execute the workflow with actual parameters:

```bash
uv run python test_workflow.py \
  src/tools/workflows/my_workflow.py \
  MyWorkflow \
  my_scan \
  --target scanme.nmap.org \
  --timeout 300
```

**The test will:**
1. ✅ Execute workflow with provided parameters
2. ✅ Validate result structure
3. ✅ Display detailed summary
4. ✅ Detect errors

#### 3. Dry Run (Simulation)

Test logic without executing actual commands:

```bash
uv run python test_workflow.py --dry-run \
  src/tools/workflows/my_workflow.py \
  MyWorkflow \
  my_scan \
  --target example.com
```

### Testing Examples

#### Example 1: Web Workflow

```bash
# Structure validation
uv run python test_workflow.py --validate src/tools/workflows/web_recon.py WebWorkflow

# Real test with target
uv run python test_workflow.py \
  src/tools/workflows/web_recon.py \
  WebWorkflow \
  web_recon \
  --target scanme.nmap.org \
  --timeout 300
```

#### Example 2: Active Directory Workflow with Credentials

```bash
uv run python test_workflow.py \
  src/tools/workflows/ad_pentest.py \
  ADPentestWorkflow \
  ad_enumeration \
  --target 192.168.1.10 \
  --domain CORP.LOCAL \
  --username admin \
  --password Password123 \
  --timeout 600
```

#### Example 3: Kubernetes Workflow

```bash
uv run python test_workflow.py \
  src/tools/workflows/k8s_audit.py \
  K8sAuditWorkflow \
  security_audit \
  --timeout 400
```

### What Tests Verify

#### Structure Validation

```
✓ All required keys present
  - workflow: my_workflow
  - target: example.com
  - steps: ['step1', 'step2', 'step3']
  - summary: ['total_findings', 'success_rate']

✓ Number of steps: 3
✓ Summary contains 2 metrics

✅ Valid workflow structure!
```

#### Execution Summary

```
Workflow: my_workflow
Target  : example.com

Executed steps (3 steps):
  ✓ port_scan
      → Ports: 12
  ✓ vuln_scan
      → Vulns: 5
  ✗ finalrecon
      (failure detected)

Global summary:
  • total_ports: 12
  • total_vulns: 5
  • success_rate: 66%
```

### Error Handling

The test automatically catches errors and displays clear messages:

```
❌ Error during workflow execution:
   TypeError: 'bool' object is not subscriptable

File "my_workflow.py", line 97
  summary["findings"] = steps["scan"]["success"]["count"]
                        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
```

**Detected error types:**
- Invalid structure (missing keys)
- Python errors (TypeError, KeyError, etc.)
- Timeouts
- Command failures
- Parsing issues

### Supported Arguments

The testing system automatically detects standard arguments:

- `--target` : Scan target
- `--timeout` : Timeout in seconds
- `--ports` : Ports to scan
- `--domain` : AD domain
- `--username` : Username
- `--password` : Password

**To add new arguments:**

Edit `test_workflow.py` lines 166-172 and add your argument.

---

## 📚 BaseWorkflow API

### Main Methods

#### `execute_step()`

Execute a step with automatic parsing.

```python
success, findings, output = self.execute_step(
    step_name="Step description",
    command="tool -flag value",
    timeout=300,
    parse_json=True,  # Automatically parse JSON
    print_progress=True  # Display progress messages
)
```

**Returns:**
- `success` (bool): True if command succeeded
- `findings` (List[Dict]): Parsed results (if parse_json=True)
- `output` (str): Raw command output

#### `create_result_dict()`

Create standardized result structure.

```python
return self.create_result_dict(
    workflow_name="my_workflow",
    target="example.com",
    steps={"step1": {...}, "step2": {...}},
    summary={"total": 10}
)
```

### Helper Methods

#### `extract_ports(findings)`

Extract ports from naabu results.

```python
ports = self.extract_ports(findings)
# → [80, 443, 8080]
```

#### `count_by_severity(findings)`

Count findings by severity (nuclei).

```python
severity_counts = self.count_by_severity(findings)
# → {"critical": 2, "high": 5, "medium": 10}
```

#### `normalize_top_ports(top_ports)`

Normalize top_ports parameter for naabu.

```python
value = self.normalize_top_ports(500)
# → "1000" (naabu only accepts 100, 1000, or full)
```

#### `write_temp_file(filename, content)`

Write a temporary file in the container.

```python
filepath = self.write_temp_file("targets.txt", "192.168.1.1\n192.168.1.10")
# → "/tmp/targets.txt"
```

---

## 💡 Workflow Examples

### Example 1: Simple Workflow (2 steps)

```python
class SimpleWorkflow(BaseWorkflow):

    def quick_scan(self, target: str, timeout: int = 600):
        steps = {}

        # Port scan
        success, findings, _ = self.execute_step(
            "Port scanning",
            f"naabu -host {target} -top-ports 100 -json",
            timeout=timeout // 2
        )
        steps["ports"] = {"success": success, "count": len(findings)}

        # Vuln scan
        success, findings, _ = self.execute_step(
            "Vulnerability scan",
            f"nuclei -target {target} -severity critical,high -json -silent",
            timeout=timeout // 2
        )
        steps["vulns"] = {"success": success, "count": len(findings)}

        return self.create_result_dict("quick_scan", target, steps, {
            "ports": steps["ports"]["count"],
            "vulns": steps["vulns"]["count"]
        })
```

### Example 2: Multi-Target Workflow

```python
class NetworkWorkflow(BaseWorkflow):

    def scan_network(self, targets: List[str], timeout: int = 1800):
        steps = {}

        # Write targets to file
        targets_file = self.write_temp_file(
            "targets.txt",
            "\n".join(targets)
        )

        # Scan all targets
        success, findings, _ = self.execute_step(
            "Network scanning",
            f"naabu -list {targets_file} -top-ports 100 -json",
            timeout=timeout
        )

        # Group by host
        by_host = {}
        for f in findings:
            host = f.get("host", "unknown")
            if host not in by_host:
                by_host[host] = []
            by_host[host].append(f["port"])

        steps["scan"] = {"success": success, "hosts": by_host}

        return self.create_result_dict("scan_network", targets, steps, {
            "total_hosts": len(by_host),
            "total_ports": len(findings)
        })
```

### Example 3: Workflow with Custom Parser

```python
class CustomWorkflow(BaseWorkflow):

    def custom_scan(self, target: str, timeout: int = 600):
        steps = {}

        # Tool that doesn't return JSON
        success, _, output = self.execute_step(
            "Custom tool scan",
            f"dirb http://{target}",
            timeout=timeout,
            parse_json=False  # No JSON
        )

        # Custom parser
        dirs_found = self._parse_dirb_output(output)

        steps["dirs"] = {"success": success, "directories": dirs_found}

        return self.create_result_dict("custom_scan", target, steps, {
            "total_dirs": len(dirs_found)
        })

    def _parse_dirb_output(self, output: str) -> List[str]:
        """Custom parser for dirb"""
        dirs = []
        for line in output.split("\n"):
            if "+ http://" in line:
                # Extract found directory
                dirs.append(line.split()[1])
        return dirs
```

---

## 🎨 Best Practices

### 1. Consistent Naming

```python
class ADPentestWorkflow(BaseWorkflow):
    def ad_enumeration(self, ...):  # ✅ Clear name
    def ad_lateral_movement(self, ...):  # ✅ Descriptive
```

### 2. Complete Documentation

```python
def my_workflow(self, target: str, timeout: int = 1200):
    """
    Clear workflow description.

    Workflow:
    1. Step 1: Description
    2. Step 2: Description

    Args:
        target: Target parameter description
        timeout: Timeout in seconds (default: 1200)

    Returns:
        Workflow results

    Use Cases:
        - Use case 1
        - Use case 2
    """
```

### 3. Error Handling

```python
# Check critical step success
if not steps["port_scan"]["success"]:
    return self.create_result_dict("my_workflow", target, steps, {
        "error": "Port scan failed, aborting"
    })
```

### 4. Intelligent Timeouts

```python
# Divide timeout between steps
success, findings, _ = self.execute_step(
    "Step 1",
    f"tool1 {target}",
    timeout=timeout // 3  # 1/3 of total timeout
)

success, findings, _ = self.execute_step(
    "Step 2",
    f"tool2 {target}",
    timeout=timeout // 3  # 1/3 of total timeout
)
```

---

## 💻 Development Workflow

Recommended development process:

```bash
# 1. Create the workflow
cp src/tools/workflows/TEMPLATE.py src/tools/workflows/my_workflow.py

# 2. Implement the logic
# ... edit my_workflow.py ...

# 3. Validate structure
uv run python test_workflow.py --validate src/tools/workflows/my_workflow.py MyWorkflow

# 4. Test with test target
uv run python test_workflow.py \
  src/tools/workflows/my_workflow.py \
  MyWorkflow \
  my_scan \
  --target scanme.nmap.org \
  --timeout 300

# 5. If OK, expose in server.py
# ... add to src/server.py ...

# 6. Test complete server
uv run python test_server.py
```

---

## 🐛 Troubleshooting

### Issue: Workflow Not Found

```bash
❌ Unable to load MyWorkflow from my_workflow.py
```

**Solution:** Check class name and file path.

### Issue: Method Not Found

```bash
❌ Method 'my_scan' not found in MyWorkflow
Available methods: ['other_scan', 'advanced_scan']
```

**Solution:** Check method name (case sensitive).

### Issue: Invalid Structure

```bash
❌ 'steps' must be a dictionary
```

**Solution:** Make sure to use `self.create_result_dict()` to return results.

### Issue: JSON Parsing Error

**Common causes:**
- Tool doesn't output JSON (set `parse_json=False`)
- Tool outputs mixed text/JSON (use custom parser)
- Malformed JSON (check tool output)

**Solution:** Use `parse_json=False` and implement custom parser if needed.

---

## 🔥 Ready-to-Use Workflows

The `TEMPLATE.py` file contains complete examples:

- **ADPentestWorkflow**: Active Directory pentesting
- **K8sAuditWorkflow**: Kubernetes security audit

Copy and adapt them to your needs!

---

## ✅ Checklist

### Before Exposing to LLM

- [ ] Copy TEMPLATE.py
- [ ] Rename class
- [ ] Implement methods
- [ ] Use execute_step() for each command
- [ ] Create summary with create_result_dict()
- [ ] Add documentation (docstring)
- [ ] `--validate` passes successfully
- [ ] Execution test passes without errors
- [ ] Result structure validated
- [ ] All steps return `success: bool`
- [ ] Summary contains key metrics
- [ ] Appropriate timeouts tested
- [ ] Import in server.py
- [ ] Expose via @mcp.tool()
- [ ] Test with test_server.py
- [ ] Update README.md

---

**With this system, creating a new workflow takes 10 minutes instead of 1 hour! 🚀**

import time
from tenacity import retry, wait_exponential, stop_after_attempt, RetryError

# ── Agent prompts ─────────────────────────────────────────────────────────────

ATTACK_SYSTEM = """You are the Attack Generator Agent of an AI Red Team system.
Your job: given a codebase, generate a comprehensive list of adversarial attack scenarios.
Think like a professional penetration tester. Be specific and technical.
Output format — use these exact headers:
## ATTACK SCENARIOS
List 6-10 concrete attack scenarios with:
- Attack Name
- Vector (e.g., HTTP endpoint, env var, file upload)
- Method (e.g., SQL injection, IDOR, path traversal)
- Likelihood: LOW/MEDIUM/HIGH/CRITICAL
Focus on the actual code provided. Do not be generic."""

EXPLOIT_SYSTEM = """You are the Exploit Finder Agent of an AI Red Team system.
Your job: given code and attack scenarios, identify ACTUAL exploitable vulnerabilities.
Look for real bugs — not theoretical ones. Cite specific lines or patterns.
Output format — use these exact headers:
## VULNERABILITIES FOUND
For each vulnerability:
- CVE/CWE reference if applicable
- Vulnerable code snippet or pattern
- Exact exploitation steps
- Severity: CRITICAL/HIGH/MEDIUM/LOW/INFO
Be precise. If something is not exploitable, say why."""

IMPACT_SYSTEM = """You are the Impact Analyzer Agent of an AI Red Team system.
Your job: assess the real-world business and technical impact of found vulnerabilities.
Think about: data exposure, financial loss, reputational damage, legal liability, lateral movement.
Output format — use these exact headers:
## IMPACT ANALYSIS
Overall Risk Score: X/10
For each vulnerability:
- Business Impact
- Technical Impact
- Affected Assets
- CVSS-like Score: X.X
- Exploitability (Easy/Medium/Hard)"""

FIX_SYSTEM = """You are the Fix Suggestion Agent of an AI Red Team system.
Your job: provide concrete, code-level remediation for each vulnerability found.
Give actual code fixes, not hand-wavy advice.
Output format — use these exact headers:
## FIX RECOMMENDATIONS
For each fix:
- Priority: IMMEDIATE/SHORT-TERM/LONG-TERM
- Affected file(s)
- Root cause
- Code fix (show before/after where possible)
- Validation/test to verify the fix works"""

RETEST_SYSTEM = """You are the Re-Test Agent of an AI Red Team system.
Your job: given the original vulnerabilities and proposed fixes, simulate re-testing.
Verify fixes are complete. Find any remaining issues or new issues introduced by fixes.
Output format — use these exact headers:
## RE-TEST RESULTS
For each original vulnerability:
- Status: FIXED / PARTIALLY FIXED / NOT FIXED / NEW ISSUE INTRODUCED
- Verification method
- Residual risk
## OVERALL SECURITY POSTURE
- Before: X/10  After: X/10
- Remaining attack surface
- Recommendations for continuous security"""


def call_agent(client, model_name: str, system_prompt: str, user_prompt: str, delay: int = 15, max_tokens: int = 500) -> str:
    """Single DeepSeek API call with aggressive rate limiting and retry logic."""
    time.sleep(delay)  # 15 second minimum gap for free tier
    
    @retry(
        wait=wait_exponential(multiplier=2, min=10, max=60),
        stop=stop_after_attempt(2),  # Reduced retries
        reraise=True,
    )
    def _call():
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,  # Parameterized max_tokens
            temperature=0.5,  # Lower temp = cheaper
        )
        return response.choices[0].message.content
    
    try:
        return _call()
    except RetryError as e:
        last_exception = e.last_attempt.exception()
        if last_exception is not None:
            return f"Error: {type(last_exception).__name__}: {str(last_exception)}"
        return f"Error: {type(e).__name__}: {str(e)}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {str(e)}"

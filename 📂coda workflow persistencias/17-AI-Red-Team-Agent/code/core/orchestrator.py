import json
from .agent_llm import call_agent
from .github_api import create_github_pr

def run_red_team(client, model_name, repo_data: dict, manual_code: str, placeholder_dict: dict, progress_bar, auto_pr: bool = False, github_token: str = ""):
    """Run streamlined agents with minimal API calls to respect free tier quotas."""

    # MINIMAL CONTEXT - Free tier must be highly aggressive
    if repo_data and "file_contents" in repo_data:
        # Only top 2 most important files to limit prompt size
        tree_str = "\n".join(repo_data.get("file_tree", [])[:15])
        files_str = "\n\n".join(
            [f"### {path}\n```\n{content[:400]}\n```"
             for path, content in list(repo_data["file_contents"].items())[:2]]
        )
        context = f"Repo: {repo_data['owner']}/{repo_data['repo']}\n\nFiles:\n{files_str}"
    else:
        context = f"Code:\n```\n{manual_code[:1000]}\n```"

    results = {}
    call_count = 0

    # ── Agent 1: ATTACK + EXPLOIT combined (saves 1 API call)
    progress_bar.progress(0.2, text="🔍 Analyzing vulnerabilities...")
    placeholder_dict["attack"].markdown(
        f'<div class="agent-card active"><span class="badge badge-running">▶ RUNNING</span><br>'
        f'<strong>⚔️ Attack & Exploit Analysis</strong><br><em>Scanning...</em></div>',
        unsafe_allow_html=True
    )

    combined_system = """You are a security analyst. Your job: 
1. Generate 3-4 attack scenarios for this codebase
2. Identify ACTUAL exploitable vulnerabilities
Format:
## ATTACK SCENARIOS
- [Name]: [description]

## VULNERABILITIES FOUND
- [CVE/CWE]: [details]"""

    attack_prompt = f"Analyze this codebase for vulnerabilities:\n\n{context}\n\nBe concise. Only list REAL exploitable issues."
    
    try:
        attack_exploit_output = call_agent(client, model_name, combined_system, attack_prompt)
        results["attack"] = attack_exploit_output
        results["exploit"] = attack_exploit_output
        call_count += 1
        
        placeholder_dict["attack"].markdown(
            f'<div class="agent-card done"><span class="badge badge-attack">✓ Analysis</span>'
            f'<br>{attack_exploit_output[:500]}</div>',
            unsafe_allow_html=True
        )
        placeholder_dict["exploit"].markdown(
            f'<div class="agent-card done"><span class="badge badge-exploit">✓ Vulnerabilities</span>'
            f'<br>{attack_exploit_output[500:1000]}</div>',
            unsafe_allow_html=True
        )
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        results["attack"] = error_msg
        results["exploit"] = error_msg
        placeholder_dict["attack"].markdown(f'<div class="agent-card error"><span class="badge badge-attack">✗ ERROR</span><br>{str(e)[:100]}</div>', unsafe_allow_html=True)
        placeholder_dict["exploit"].markdown(f'<div class="agent-card error"><span class="badge badge-exploit">✗ ERROR</span><br>{str(e)[:100]}</div>', unsafe_allow_html=True)

    # ── Agent 2: IMPACT + FIX combined (saves 1 API call)
    progress_bar.progress(0.5, text="💥 Assessing impact and fixes...")
    placeholder_dict["impact"].markdown(
        f'<div class="agent-card active"><span class="badge badge-running">▶ RUNNING</span><br>'
        f'<strong>💥 Impact & Fixes</strong><br><em>Processing...</em></div>',
        unsafe_allow_html=True
    )

    combined_system2 = """You are a security remediator.
1. Assess business impact (severity score X/10)
2. Provide minimal code fixes

Format:
## IMPACT: [severity score]
[brief analysis]

## FIXES
- [fix 1]
- [fix 2]"""

    impact_prompt = f"For these vulnerabilities:\n\n{attack_exploit_output[:600]}\n\nProvide impact and fixes. Be extremely concise."
    
    try:
        impact_fix_output = call_agent(client, model_name, combined_system2, impact_prompt, delay=15)
        results["impact"] = impact_fix_output
        results["fix"] = impact_fix_output
        call_count += 1
        
        placeholder_dict["impact"].markdown(
            f'<div class="agent-card done"><span class="badge badge-impact">✓ Impact</span>'
            f'<br>{impact_fix_output[:400]}</div>',
            unsafe_allow_html=True
        )
        placeholder_dict["fix"].markdown(
            f'<div class="agent-card done"><span class="badge badge-fix">✓ Fixes</span>'
            f'<br>{impact_fix_output[400:800]}</div>',
            unsafe_allow_html=True
        )
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        results["impact"] = error_msg
        results["fix"] = error_msg
        placeholder_dict["impact"].markdown(f'<div class="agent-card error"><span class="badge badge-impact">✗ ERROR</span><br>{str(e)[:100]}</div>', unsafe_allow_html=True)
        placeholder_dict["fix"].markdown(f'<div class="agent-card error"><span class="badge badge-fix">✗ ERROR</span><br>{str(e)[:100]}</div>', unsafe_allow_html=True)

    # ── Agent 3: RETEST (minimal single call)
    progress_bar.progress(0.8, text="🔄 Re-testing...")
    placeholder_dict["retest"].markdown(
        f'<div class="agent-card active"><span class="badge badge-running">▶ RUNNING</span><br>'
        f'<strong>🔄 Re-Test</strong><br><em>Verifying...</em></div>',
        unsafe_allow_html=True
    )

    retest_system = """You are a security re-tester. 
Verify if proposed fixes would resolve vulnerabilities.
Format:
## RE-TEST RESULTS
- [vuln]: FIXED / NOT FIXED"""

    retest_prompt = f"Fixes:\n{impact_fix_output[:400]}\n\nAgainst:\n{attack_exploit_output[:400]}\n\nVerify status."
    
    try:
        retest_output = call_agent(client, model_name, retest_system, retest_prompt, delay=15)
        results["retest"] = retest_output
        call_count += 1
        
        placeholder_dict["retest"].markdown(
            f'<div class="agent-card done"><span class="badge badge-retest">✓ Re-Test</span>'
            f'<br>{retest_output[:500]}</div>',
            unsafe_allow_html=True
        )
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        results["retest"] = error_msg
        placeholder_dict["retest"].markdown(f'<div class="agent-card error"><span class="badge badge-retest">✗ ERROR</span><br>{str(e)[:100]}</div>', unsafe_allow_html=True)

    # ── Agent 4: Auto PR
    if auto_pr and repo_data and github_token:
        progress_bar.progress(0.9, text="🚀 Generating Patch & PR...")
        placeholder_dict["pr"].markdown(
            f'<div class="agent-card active"><span class="badge badge-running">▶ RUNNING</span><br>'
            f'<strong>🚀 Patch & PR</strong><br><em>Generating fixes...</em></div>',
            unsafe_allow_html=True
        )

        pr_system = """You are the Auto-Patch Agent.
Generate a valid JSON object containing full repaired code for affected files based on the suggested fixes. 
Response MUST be valid JSON format:
{
  "files": [
    {"path": "exact/file/path.py", "content": "full updated code including all original unmodified parts"}
  ]
}
Return raw JSON ONLY. No markdown block backticks."""

        pr_prompt = f"Original Files:\n{context}\n\nApply these fixes:\n{impact_fix_output[:500]}\n\nReturn JSON ONLY."

        try:
            pr_output = call_agent(client, model_name, pr_system, pr_prompt, delay=15, max_tokens=2500)
            call_count += 1
            
            json_str = pr_output.strip()
            if json_str.startswith("```json"): json_str = json_str[7:-3]
            elif json_str.startswith("```"): json_str = json_str[3:-3]
            
            pr_data = json.loads(json_str)
            new_files = {f["path"]: f["content"] for f in pr_data.get("files", [])}
            
            if new_files:
                pr_url = create_github_pr(
                    owner=repo_data["owner"], 
                    repo=repo_data["repo"], 
                    token=github_token, 
                    new_files=new_files, 
                    commit_msg="Auto-fix vulnerabilities from AI Red Team", 
                    pr_title="🔴 AI Red Team: Vulnerability Auto-Fix", 
                    pr_body="This PR contains automated security fixes generated by the AI Red Team System.\n\n### Fix Details\n" + impact_fix_output[:1000]
                )
                
                if pr_url.startswith("http"):
                    results["pr"] = f"✅ Pull Request Created: {pr_url}"
                    placeholder_dict["pr"].markdown(f'<div class="agent-card done"><span class="badge badge-pr">✓ PR Created</span><br><a href="{pr_url}" target="_blank" style="color:#00ff88;">View Pull Request</a></div>', unsafe_allow_html=True)
                else:
                    results["pr"] = f"❌ PR Error: {pr_url}"
                    placeholder_dict["pr"].markdown(f'<div class="agent-card error"><span class="badge badge-pr">✗ ERROR</span><br>{pr_url}</div>', unsafe_allow_html=True)
            else:
                results["pr"] = "❌ Failed to generate any file changes."
                placeholder_dict["pr"].markdown(f'<div class="agent-card error"><span class="badge badge-pr">✗ ERROR</span><br>No valid changes generated.</div>', unsafe_allow_html=True)
                
        except Exception as e:
            results["pr"] = f"❌ PR Error: {str(e)}"
            placeholder_dict["pr"].markdown(f'<div class="agent-card error"><span class="badge badge-pr">✗ ERROR</span><br>{str(e)[:100]}</div>', unsafe_allow_html=True)
            
    elif auto_pr:
        placeholder_dict["pr"].markdown(f'<div class="agent-card error"><span class="badge badge-pr">✗ SKIPPED</span><br>Missing GitHub token or repo context.</div>', unsafe_allow_html=True)
    else:
        results["pr"] = "Auto PR disabled."
        placeholder_dict["pr"].markdown(f'<div class="agent-card done"><span class="badge badge-pr">✓ SKIPPED</span><br>Auto PR disabled.</div>', unsafe_allow_html=True)

    progress_bar.progress(1.0, text=f"✅ Complete ({call_count} API calls)")
    return results

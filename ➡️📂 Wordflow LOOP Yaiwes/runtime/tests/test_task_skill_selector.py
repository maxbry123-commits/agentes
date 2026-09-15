from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "src" / "core" / "task_skill_selector.py"
spec = importlib.util.spec_from_file_location("task_skill_selector", P)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)

def catalog():
    return [
        {"name":"hf-cli","version":"1","origin":"hf","path":"skills/hf-cli/SKILL.md","tags":["huggingface","skills","download","general"],"verified":True},
        {"name":"frontend-browser","version":"1","origin":"hf","path":"skills/frontend-browser/SKILL.md","tags":["frontend","browser","ui","mobile"],"verified":True},
        {"name":"playwright","version":"1","origin":"hf","path":"skills/playwright/SKILL.md","tags":["frontend","browser","test","mobile"],"verified":True},
        {"name":"accessibility","version":"1","origin":"hf","path":"skills/a11y/SKILL.md","tags":["frontend","ui","test"],"verified":True},
        {"name":"git-safe","version":"1","origin":"hf","path":"skills/git-safe/SKILL.md","tags":["git","general"],"verified":True},
        {"name":"unverified","version":"1","origin":"hf","path":"skills/no/SKILL.md","tags":["frontend"],"verified":False},
    ]

def test_selects_three_to_five_relevant_verified():
    d=m.select_skills(task_id="t1",task="frontend browser UI mobile test",profile="frontend",catalog=catalog())
    assert d.passed and 3 <= len(d.selected) <= 5
    assert all(s.verified for s in d.selected)
    assert "unverified" not in [s.name for s in d.selected]

def test_fails_closed_below_minimum():
    d=m.select_skills(task_id="t2",task="backend database migration",profile="backend",catalog=catalog())
    assert not d.passed
    assert d.reason.startswith("INSUFFICIENT_RELEVANT_VERIFIED_SKILLS")

def test_rejects_duplicate_names():
    c=catalog(); c.append(dict(c[0]))
    try:
        m.select_skills(task_id="t3",task="hf skills",profile="general",catalog=c)
    except m.SkillSelectionError as e:
        assert str(e)=="DUPLICATE_SKILL_NAME"
    else:
        raise AssertionError("expected duplicate rejection")

def test_deterministic_order():
    a=m.select_skills(task_id="t4",task="frontend browser ui mobile test",profile="frontend",catalog=catalog())
    b=m.select_skills(task_id="t4",task="frontend browser ui mobile test",profile="frontend",catalog=list(reversed(catalog())))
    assert [x.name for x in a.selected] == [x.name for x in b.selected]

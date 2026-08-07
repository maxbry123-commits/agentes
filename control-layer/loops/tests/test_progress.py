from loops.progress import ProgressEvaluator, AdaptiveIterationController


def test_numeric_and_tests():
    ev = ProgressEvaluator()
    p = ev.evaluate(kind="numeric", value=0.4)
    assert 0.39 < p.progress_score < 0.41
    t = ev.evaluate(kind="tests", value={"passed": 8, "total": 10})
    assert abs(t.progress_score - 0.8) < 0.01


def test_adaptive_stall():
    c = AdaptiveIterationController(max_iter=8, stall_limit=2)
    ev = ProgressEvaluator()
    low = ev.evaluate(kind="numeric", value=0.05, threshold=0.1)
    a1 = c.advise(low, 1)
    a2 = c.advise(low, 2)
    assert a2.suggest_action == "CHANGE_STRATEGY"


def test_adaptive_close_excellent():
    c = AdaptiveIterationController()
    ev = ProgressEvaluator()
    p = ev.evaluate(kind="numeric", value=0.98)
    a = c.advise(p, 1)
    assert a.suggest_action == "CLOSE"
    assert a.continue_loop is False

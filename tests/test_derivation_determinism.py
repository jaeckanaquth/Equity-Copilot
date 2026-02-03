from core.derivations.assemble import build_revenue_yoy_metric_set


def test_deterministic_output(snapshot_factory):
    s1 = snapshot_factory(as_of="2024-03-31T00:00:00Z", revenue_fy=100)
    s2 = snapshot_factory(as_of="2025-03-31T00:00:00Z", revenue_fy=120)

    d1 = build_revenue_yoy_metric_set([s1, s2])
    d2 = build_revenue_yoy_metric_set([s1, s2])

    assert d1.metrics[0].value == d2.metrics[0].value
    assert d1.metrics[0].formula == d2.metrics[0].formula

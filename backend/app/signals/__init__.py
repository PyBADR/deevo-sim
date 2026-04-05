"""signals — Live Signal Layer for Impact Observatory (MVP: banking + fintech).

Flow:
    raw dict → normalizer → scorer → seed_generator → hitl → run_unified_pipeline

HITL is mandatory. Nothing enters the pipeline without an APPROVED ScenarioSeed.
"""

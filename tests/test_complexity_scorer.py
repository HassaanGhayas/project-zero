from src.utils.complexity_scorer import complexity_score


def test_short_simple_text_scores_zero():
    assert complexity_score("Fix the login bug") == 0


def test_long_text_adds_one():
    text = " ".join(["word"] * 201)
    assert complexity_score(text) >= 1


def test_api_mention_adds_one():
    assert complexity_score("Integrate with the Stripe API for payments") >= 1


def test_multiple_steps_adds_one():
    assert complexity_score("First do X, then do Y, next do Z") >= 1


def test_multiple_stakeholders_adds_one():
    assert complexity_score("Coordinate with the frontend team and backend database") >= 1


def test_complex_task_scores_three_or_more():
    text = (
        "Integrate with Stripe API to process payments. "
        "First create the endpoint, then add webhook handling, next update the database. "
        "Coordinate with the frontend team and backend system. " * 20
    )
    assert complexity_score(text) >= 3


def test_api_keyword_case_insensitive():
    assert complexity_score("Use the REST api for this") >= 1

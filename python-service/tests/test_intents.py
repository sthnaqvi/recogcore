from recog_core.conversation.intents import match_intent


def test_match_intent_how_are_you():
    assert match_intent("how are you today") is not None


def test_match_intent_weather():
    response = match_intent("what's the weather like")
    assert response is not None
    assert "weather" in response.lower()


def test_match_intent_goodbye():
    assert match_intent("okay bye") is not None


def test_match_intent_thanks():
    assert match_intent("thanks a lot") is not None


def test_match_intent_who_are_you():
    response = match_intent("who are you")
    assert response is not None
    assert "recogcore" in response.lower()


def test_match_intent_returns_none_for_unmatched_text():
    assert match_intent("tell me a story about dragons") is None


def test_match_intent_is_case_insensitive():
    assert match_intent("HOW ARE YOU") is not None

from unittest.mock import patch

from recog_core.conversation.responder import NO_MATCH_RESPONSE, get_response


def test_rule_match_short_circuits_before_llm():
    with patch("recog_core.conversation.llm_responder.get_llm_response") as mock_llm:
        response = get_response("how are you", mode="llm")

    assert "great" in response.lower() or "well" in response.lower()
    mock_llm.assert_not_called()


def test_rules_mode_falls_back_to_no_match_response_without_calling_llm():
    with patch("recog_core.conversation.llm_responder.get_llm_response") as mock_llm:
        response = get_response("tell me a story about dragons", mode="rules")

    assert response == NO_MATCH_RESPONSE
    mock_llm.assert_not_called()


def test_llm_mode_falls_through_when_no_rule_matches():
    with patch(
        "recog_core.conversation.llm_responder.get_llm_response", return_value="A mocked LLM reply."
    ) as mock_llm:
        response = get_response("tell me a story about dragons", mode="llm")

    mock_llm.assert_called_once_with("tell me a story about dragons")
    assert response == "A mocked LLM reply."

from unittest.mock import MagicMock, patch

from src.rag.generate import generate_answer


def _mock_message(text: str) -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = text
    message = MagicMock()
    message.content = [block]
    return message


@patch("src.rag.generate._client")
def test_generate_answer_returns_text(mock_client_factory):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_message("This is a test answer [21 CFR § 7.1].")
    mock_client_factory.return_value = mock_client

    chunks = [{"text": "Some regulation text.", "metadata": {"citation": "21 CFR § 7.1"}}]
    answer = generate_answer("What does this say?", chunks)

    assert answer == "This is a test answer [21 CFR § 7.1]."
    mock_client.messages.create.assert_called_once()


@patch("src.rag.generate._client")
def test_generate_answer_includes_history(mock_client_factory):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_message("Follow-up answer.")
    mock_client_factory.return_value = mock_client

    chunks = [{"text": "Some text.", "metadata": {"citation": "21 CFR § 7.1"}}]
    generate_answer("What about Z?", chunks, history=[("What is X?", "X is Y.")])

    messages = mock_client.messages.create.call_args.kwargs["messages"]
    assert messages[0] == {"role": "user", "content": "What is X?"}
    assert messages[1] == {"role": "assistant", "content": "X is Y."}

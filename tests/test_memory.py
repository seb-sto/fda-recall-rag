from src.rag.memory import MAX_TURNS, add_turn, get_history


def test_add_and_get_history():
    session_id = "test-session-1"
    add_turn(session_id, "Q1", "A1")
    add_turn(session_id, "Q2", "A2")
    assert get_history(session_id) == [("Q1", "A1"), ("Q2", "A2")]


def test_history_window_drops_oldest():
    session_id = "test-session-2"
    for i in range(MAX_TURNS + 2):
        add_turn(session_id, f"Q{i}", f"A{i}")
    history = get_history(session_id)
    assert len(history) == MAX_TURNS
    assert history[0] == ("Q2", "A2")

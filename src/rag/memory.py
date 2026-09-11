from collections import defaultdict, deque

MAX_TURNS = 5

_sessions: dict[str, deque[tuple[str, str]]] = defaultdict(lambda: deque(maxlen=MAX_TURNS))


def get_history(session_id: str) -> list[tuple[str, str]]:
    return list(_sessions[session_id])


def add_turn(session_id: str, question: str, answer: str) -> None:
    _sessions[session_id].append((question, answer))

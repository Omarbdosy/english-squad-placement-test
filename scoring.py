"""Adaptive placement logic for English Squad.
The CEFR mapping below is a working assessment calibration, not a claim made by the source books.
"""
LEVELS = [f"{c}.{i}" for c in ("A1", "A2", "B1", "B2", "C1", "C2") for i in (1, 2, 3)]
SKILLS = ["Grammar", "Vocabulary", "Reading"]

MAX_MINUTES = 40
QUESTIONS_PER_LEVEL = 6          # 2 per skill
MAX_QUESTIONS = len(LEVELS) * QUESTIONS_PER_LEVEL
LEVEL_PASS = 4                   # 4/6 = 67%
STOP_AFTER_WRONG = 4

# Skill reporting: highest level with >=50% at that level, plus >=60% across that and two lower levels.
SKILL_HERE_PASS = 0.50
SKILL_WINDOW_PASS = 0.60
MIN_SKILL_AT_LEVEL = 2
WINDOW = 3


def level_index(level):
    return LEVELS.index(level)


def current_level(history):
    """Highest level index already attempted, based on completed blocks."""
    blocks = []
    for i in range(0, len(history), QUESTIONS_PER_LEVEL):
        block = history[i:i + QUESTIONS_PER_LEVEL]
        if len(block) < QUESTIONS_PER_LEVEL:
            return len(blocks)
        blocks.append(block)
        if sum(bool(a["correct"]) for a in block) < LEVEL_PASS:
            return len(blocks) - 1
    return min(len(blocks), len(LEVELS) - 1)


def next_step(history):
    if len(history) >= MAX_QUESTIONS:
        return "stop", "question limit"
    if any(not a["correct"] for a in history[-STOP_AFTER_WRONG:]) and len(history) >= STOP_AFTER_WRONG:
        if all(not a["correct"] for a in history[-STOP_AFTER_WRONG:]):
            return "stop", "wrong streak"

    # Work out which sublevel should be tested next.
    completed = len(history) // QUESTIONS_PER_LEVEL
    remainder = len(history) % QUESTIONS_PER_LEVEL
    if remainder:
        return "ask", min(completed, len(LEVELS) - 1)
    if completed >= len(LEVELS):
        return "stop", "top reached"
    if completed == 0:
        return "ask", 0
    last = history[-QUESTIONS_PER_LEVEL:]
    if sum(bool(a["correct"]) for a in last) >= LEVEL_PASS:
        return "ask", completed
    return "stop", "level not secured"


def _place_skill(answers):
    by = {}
    for a in answers:
        by.setdefault(level_index(a["level"]), []).append(bool(a["correct"]))
    best = 0
    for i in range(len(LEVELS)):
        here = by.get(i, [])
        if len(here) < MIN_SKILL_AT_LEVEL or sum(here) / len(here) < SKILL_HERE_PASS:
            continue
        window = [x for j in range(max(0, i - WINDOW + 1), i + 1) for x in by.get(j, [])]
        if window and sum(window) / len(window) >= SKILL_WINDOW_PASS:
            best = i
    return best


def summarize(history):
    # Overall = highest fully tested level that met 4/6. If A1.1 fails, return A1.1.
    best = 0
    for start in range(0, len(history), QUESTIONS_PER_LEVEL):
        block = history[start:start + QUESTIONS_PER_LEVEL]
        if len(block) < QUESTIONS_PER_LEVEL:
            break
        if sum(bool(a["correct"]) for a in block) >= LEVEL_PASS:
            best = min(start // QUESTIONS_PER_LEVEL, len(LEVELS) - 1)
        else:
            break
    out = {"overall": LEVELS[best]}
    for skill in SKILLS:
        h = [a for a in history if a["skill"] == skill]
        i = _place_skill(h) if h else best
        # Never report a skill implausibly far from the measured overall level.
        i = max(best - 2, min(best + 2, i))
        out[skill] = LEVELS[i]
    return out

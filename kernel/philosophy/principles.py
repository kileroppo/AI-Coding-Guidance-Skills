"""Operational heuristics derived from philosophy (dao.md, strategy.md).

These functions translate philosophical principles into concrete decision
signals that the kernel uses during execution.
"""

from collections import Counter


def should_stop_iterating(state: dict, reflections: list[dict]) -> bool:
    """Know when to stop to avoid danger.

    Returns True if diminishing returns detected:
    - Same errors repeating 3+ times in recent reflections
    - tasks_done has not changed across last 5 progress_history entries

    Args:
        state: The current state dict (may contain progress_history).
        reflections: List of recent reflection dicts.

    Returns:
        True if iteration should stop due to diminishing returns.
    """
    # Check for repeating errors in reflections
    if reflections:
        error_counts: Counter = Counter()
        for reflection in reflections:
            for issue in reflection.get("issues", []):
                error_counts[issue] += 1
        for _error, count in error_counts.items():
            if count >= 3:
                return True

    # Check for stalled progress_history
    progress_history = state.get("progress_history", [])
    if len(progress_history) >= 5:
        last_five = progress_history[-5:]
        if len(set(last_five)) == 1:
            return True

    return False


def should_simplify(task_complexity: int, failure_count: int) -> bool:
    """The greatest Dao is the simplest.

    Returns True if failure_count >= 3, suggesting the task should be split.
    task_complexity is number of steps/subtasks (used for logging context).

    Args:
        task_complexity: Number of steps/subtasks in the task.
        failure_count: Number of consecutive failures for this task.

    Returns:
        True if the task should be simplified (split).
    """
    return failure_count >= 3


def should_retreat(node_id: str, consecutive_failures: int, max_retries: int = 5) -> bool:
    """Of the 36 stratagems, retreat is best.

    Returns True if consecutive_failures >= max_retries for the node.
    Signals the runner should skip this node and move on.

    Args:
        node_id: The node identifier.
        consecutive_failures: Number of consecutive failures for this node.
        max_retries: Maximum retries allowed (default 5).

    Returns:
        True if the node should be abandoned.
    """
    return consecutive_failures >= max_retries


def assess_terrain(goal: str, available_skills: list[dict]) -> dict:
    """Know heaven and know earth.

    Tokenizes goal into words, matches against skill tags and description words.

    Args:
        goal: The goal string to assess.
        available_skills: List of skill dicts with 'name', 'tags', 'description' fields.

    Returns:
        Dict with coverage_score (float 0.0-1.0), covered (list of skill names),
        gaps (list of goal keywords with no matching skill),
        recommendation ("proceed"|"proceed_with_caution"|"reconsider").
    """
    # Tokenize goal into keywords (lowercase, non-empty, length > 2)
    goal_keywords = [
        w for w in goal.lower().split() if len(w) > 2
    ]

    if not goal_keywords:
        return {
            "coverage_score": 0.0,
            "covered": [],
            "gaps": [],
            "recommendation": "reconsider",
        }

    # Build a set of all skill words (from tags and descriptions)
    skill_words: set = set()
    skill_names_matched: list = []
    for skill in available_skills:
        tags = [t.lower() for t in skill.get("tags", [])]
        desc_words = [w.lower() for w in skill.get("description", "").split() if len(w) > 2]
        skill_words.update(tags)
        skill_words.update(desc_words)

    # Match keywords against skill words
    covered_keywords: list = []
    gaps: list = []
    for keyword in goal_keywords:
        if keyword in skill_words:
            covered_keywords.append(keyword)
        else:
            gaps.append(keyword)

    # Determine which skills contributed to coverage
    covered_skill_names: list = []
    for skill in available_skills:
        tags = [t.lower() for t in skill.get("tags", [])]
        desc_words = [w.lower() for w in skill.get("description", "").split() if len(w) > 2]
        all_skill_words = set(tags + desc_words)
        if any(kw in all_skill_words for kw in covered_keywords):
            covered_skill_names.append(skill.get("name", ""))

    coverage_score = len(covered_keywords) / len(goal_keywords)

    # Determine recommendation
    if coverage_score >= 0.7:
        recommendation = "proceed"
    elif coverage_score >= 0.4:
        recommendation = "proceed_with_caution"
    else:
        recommendation = "reconsider"

    return {
        "coverage_score": coverage_score,
        "covered": covered_skill_names,
        "gaps": gaps,
        "recommendation": recommendation,
    }

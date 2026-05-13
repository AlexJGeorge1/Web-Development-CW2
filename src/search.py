"""
Search module: AND queries and phrase queries over the inverted index.

AND queries return URLs that contain ALL search terms.
Phrase queries additionally check that the terms appear in consecutive
positions, using the positional data stored in the index.
"""


def and_query(index: dict, terms: list[str]) -> list[str]:
    """
    Return URLs that contain ALL of the given terms.

    Uses set intersection across the URL sets for each term.
    If any term is not in the index, returns an empty list
    (since no document can match all terms).

    Args:
        index: the positional inverted index.
        terms: a list of search terms (already tokenised/lowercased).

    Returns:
        A list of URLs containing every term.
    """
    if not terms:
        return []

    # get the set of URLs for the first term
    first_term = terms[0]
    if first_term not in index:
        return []

    result_urls = set(index[first_term].keys())

    # intersect with URL sets for the remaining terms
    for term in terms[1:]:
        if term not in index:
            return []
        result_urls = result_urls & set(index[term].keys())

    return list(result_urls)


def phrase_query(index: dict, terms: list[str]) -> list[str]:
    """
    Return URLs where the terms appear as a consecutive phrase.

    First narrows candidates using AND logic, then checks positional
    data to verify that each term appears exactly one position after
    the previous term.

    For example, if terms are ["the", "world"], we look for any URL
    where "the" appears at position N and "world" appears at position
    N+1.

    Args:
        index: the positional inverted index.
        terms: a list of search terms forming the phrase.

    Returns:
        A list of URLs where the exact phrase appears.
    """
    if not terms:
        return []

    if len(terms) == 1:
        return and_query(index, terms)

    # first get candidate URLs that contain all terms
    candidates = and_query(index, terms)
    matches = []

    for url in candidates:
        # get position lists for each term in this URL
        position_lists = []
        for term in terms:
            positions = index[term][url]["positions"]
            position_lists.append(positions)

        # check if there is a consecutive sequence
        if has_consecutive_positions(position_lists):
            matches.append(url)

    return matches


def has_consecutive_positions(position_lists: list[list[int]]) -> bool:
    """
    Check whether there exists a sequence of positions where each
    successive position is exactly one more than the previous.

    For each starting position of the first term, we check whether
    position+1 exists in the second term's positions, position+2
    in the third term's positions, and so on.

    Args:
        position_lists: a list of position lists, one per term.

    Returns:
        True if a consecutive sequence exists, False otherwise.
    """
    if not position_lists:
        return False

    # convert all lists after the first to sets for O(1) lookup
    position_sets = [set(positions) for positions in position_lists[1:]]

    # try each starting position from the first term
    for start_pos in position_lists[0]:
        found = True
        for offset, pos_set in enumerate(position_sets, start=1):
            if (start_pos + offset) not in pos_set:
                found = False
                break
        if found:
            return True

    return False


def edit_distance(s1: str, s2: str) -> int:
    """
    Compute the Levenshtein edit distance between two strings.

    Uses dynamic programming to find the minimum number of single-character
    insertions, deletions, or substitutions needed to transform s1 into s2.

    Args:
        s1: the first string.
        s2: the second string.

    Returns:
        The minimum edit distance (0 means the strings are identical).
    """
    m, n = len(s1), len(s2)

    prev = list(range(n + 1))
    curr = [0] * (n + 1)

    for i in range(1, m + 1):
        curr[0] = i
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev, curr = curr, prev

    return prev[n]


def suggest_terms(index: dict, term: str, max_suggestions: int = 5) -> list[str]:
    """
    Suggest index terms similar to the given term using edit distance.

    Scans all words in the index and returns the closest matches,
    filtered to only include terms within a reasonable edit distance
    (at most half the length of the query term plus one).

    Args:
        index: the positional inverted index.
        term: the misspelled or unrecognised query term.
        max_suggestions: maximum number of suggestions to return.

    Returns:
        A list of suggested terms sorted by edit distance (closest first).
    """
    if not term or not index:
        return []

    threshold = max(len(term) // 2 + 1, 2)

    scored = []
    for word in index:
        if abs(len(word) - len(term)) > threshold:
            continue
        dist = edit_distance(term, word)
        if 0 < dist <= threshold:
            scored.append((dist, word))

    scored.sort(key=lambda x: (x[0], x[1]))

    return [word for _, word in scored[:max_suggestions]]

"""
Fuzzy matching utilities for customer identification.
Uses Levenshtein distance for similarity scoring.
"""

from typing import Tuple


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Levenshtein distance (number of edits needed to transform s1 to s2)

    Example:
        >>> levenshtein_distance("kitten", "sitting")
        3
        >>> levenshtein_distance("hello", "hello")
        0
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)

    for i, c1 in enumerate(s1):
        current_row = [i + 1]

        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, or substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)

            current_row.append(min(insertions, deletions, substitutions))

        previous_row = current_row

    return previous_row[-1]


def similarity_score(s1: str, s2: str) -> float:
    """
    Calculate similarity score between two strings (0.0 to 1.0).

    Args:
        s1: First string
        s2: Second string

    Returns:
        Similarity score (1.0 = exact match, 0.0 = completely different)

    Example:
        >>> similarity_score("hello", "hello")
        1.0
        >>> similarity_score("hello", "hallo")
        0.8
    """
    if not s1 or not s2:
        return 0.0

    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))

    if max_len == 0:
        return 1.0

    return 1.0 - (distance / max_len)


def fuzzy_match_email(email1: str, email2: str, threshold: float = 0.85) -> float:
    """
    Fuzzy match two email addresses.

    Args:
        email1: First email address
        email2: Second email address
        threshold: Minimum similarity threshold (default 0.85)

    Returns:
        Similarity score (0.0 to 1.0)

    Example:
        >>> fuzzy_match_email("alice@example.com", "ALICE@EXAMPLE.COM")
        1.0
        >>> fuzzy_match_email("alice@example.com", "allice@example.com")
        0.94
    """
    # Normalize emails (lowercase)
    email1_norm = email1.lower().strip()
    email2_norm = email2.lower().strip()

    # Exact match
    if email1_norm == email2_norm:
        return 1.0

    # Calculate similarity
    return similarity_score(email1_norm, email2_norm)


def fuzzy_match_phone(phone1: str, phone2: str, threshold: float = 0.90) -> float:
    """
    Fuzzy match two phone numbers.

    Args:
        phone1: First phone number
        phone2: Second phone number
        threshold: Minimum similarity threshold (default 0.90)

    Returns:
        Similarity score (0.0 to 1.0)

    Example:
        >>> fuzzy_match_phone("+14155238886", "+1-415-523-8886")
        1.0
        >>> fuzzy_match_phone("+14155238886", "+14155239999")
        0.83
    """
    from .phone_normalizer import normalize_phone_number

    try:
        # Try to normalize both numbers
        phone1_norm = normalize_phone_number(phone1)
        phone2_norm = normalize_phone_number(phone2)

        # Exact match
        if phone1_norm == phone2_norm:
            return 1.0

        # Calculate similarity on normalized numbers
        return similarity_score(phone1_norm, phone2_norm)

    except ValueError:
        # If normalization fails, compare raw strings
        # Remove all non-digit characters
        import re
        phone1_digits = re.sub(r'\D', '', phone1)
        phone2_digits = re.sub(r'\D', '', phone2)

        if phone1_digits == phone2_digits:
            return 1.0

        return similarity_score(phone1_digits, phone2_digits)


def fuzzy_match_name(name1: str, name2: str, threshold: float = 0.80) -> Tuple[float, bool]:
    """
    Fuzzy match two names.

    Args:
        name1: First name
        name2: Second name
        threshold: Minimum similarity threshold (default 0.80)

    Returns:
        Tuple of (similarity_score, meets_threshold)

    Example:
        >>> fuzzy_match_name("Alice Johnson", "alice johnson")
        (1.0, True)
        >>> fuzzy_match_name("Alice Johnson", "Alicia Johnston")
        (0.87, True)
        >>> fuzzy_match_name("Alice Johnson", "Bob Smith")
        (0.15, False)
    """
    # Normalize names (lowercase, strip whitespace)
    name1_norm = name1.lower().strip()
    name2_norm = name2.lower().strip()

    # Exact match
    if name1_norm == name2_norm:
        return 1.0, True

    # Split into parts (first, last)
    parts1 = name1_norm.split()
    parts2 = name2_norm.split()

    # If same number of parts, check each part
    if len(parts1) == len(parts2):
        part_similarities = []
        for p1, p2 in zip(parts1, parts2):
            part_similarities.append(similarity_score(p1, p2))

        avg_similarity = sum(part_similarities) / len(part_similarities)
        return avg_similarity, avg_similarity >= threshold

    # Different number of parts - check overall similarity
    overall_similarity = similarity_score(name1_norm, name2_norm)
    return overall_similarity, overall_similarity >= threshold


def fuzzy_match_customer(
    email1: str,
    email2: str,
    name1: str = None,
    name2: str = None,
    phone1: str = None,
    phone2: str = None
) -> Tuple[float, str]:
    """
    Comprehensive fuzzy matching for customer identification.

    Args:
        email1: First customer email
        email2: Second customer email
        name1: First customer name (optional)
        name2: Second customer name (optional)
        phone1: First customer phone (optional)
        phone2: Second customer phone (optional)

    Returns:
        Tuple of (confidence_score, match_reason)

    Example:
        >>> fuzzy_match_customer("alice@example.com", "alice@example.com", "Alice", "Alice")
        (1.0, 'exact_email_match')
    """
    # Email exact match - highest confidence
    if email1.lower() == email2.lower():
        return 1.0, "exact_email_match"

    # Phone exact match - high confidence
    if phone1 and phone2:
        phone_similarity = fuzzy_match_phone(phone1, phone2)
        if phone_similarity >= 0.95:
            return 0.98, "exact_phone_match"

    # Email fuzzy match - moderate confidence
    email_similarity = fuzzy_match_email(email1, email2)
    if email_similarity >= 0.90:
        return email_similarity, "fuzzy_email_match"

    # Phone fuzzy match with name confirmation - moderate confidence
    if phone1 and phone2 and name1 and name2:
        phone_similarity = fuzzy_match_phone(phone1, phone2)
        name_similarity, name_meets_threshold = fuzzy_match_name(name1, name2)

        if phone_similarity >= 0.85 and name_meets_threshold:
            combined_score = (phone_similarity * 0.6 + name_similarity * 0.4)
            return combined_score, "phone_and_name_match"

    # Low confidence - not a match
    return 0.0, "no_match"


def should_confirm_identity(
    existing_name: str,
    new_name: str,
    confidence_score: float,
    threshold: float = 0.85
) -> bool:
    """
    Determine if identity confirmation prompt should be shown to agent.

    Args:
        existing_name: Name from existing customer record
        new_name: Name from new interaction
        confidence_score: Confidence score from matching (0.0 to 1.0)
        threshold: Confidence threshold for auto-match (default 0.85)

    Returns:
        True if identity confirmation is needed, False if confident match

    Example:
        >>> should_confirm_identity("Alice Johnson", "Alice Johnson", 0.95)
        False  # High confidence, same name
        >>> should_confirm_identity("Alice Johnson", "Alicia J", 0.75)
        True  # Low confidence, different name
    """
    # High confidence and names match - no confirmation needed
    if confidence_score >= threshold:
        name_similarity, _ = fuzzy_match_name(existing_name, new_name)
        if name_similarity >= 0.90:
            return False

    # Low to moderate confidence - confirmation needed
    if confidence_score < threshold:
        return True

    # High confidence but names differ - confirmation recommended
    name_similarity, _ = fuzzy_match_name(existing_name, new_name)
    if name_similarity < 0.80:
        return True

    return False

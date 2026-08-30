import re
from typing import Literal


ConversationIntent = Literal[
    "greeting",
    "thanks",
    "goodbye",
    "joke",
    "joke_reaction",
    "insurance_claim",
    "unrelated",
    "unknown",
]


GREETING_PATTERNS = [
    r"\bhello\b",
    r"\bhi\b",
    r"\bhey\b",
    r"\bgood morning\b",
    r"\bgood afternoon\b",
    r"\bgood evening\b",
    r"\bhow are you\b",
    r"\bhow's it going\b",
    r"\bhow are things\b",
]


THANKS_PATTERNS = [
    r"\bthank you\b",
    r"\bthanks\b",
    r"\bappreciate it\b",
]


GOODBYE_PATTERNS = [
    r"\bbye\b",
    r"\bgoodbye\b",
    r"\bsee you\b",
    r"\btalk to you later\b",
    r"\bhave a good day\b",
]


JOKE_PATTERNS = [
    r"\btell me a joke\b",
    r"\btell us a joke\b",
    r"\bcan you tell me a joke\b",
    r"\bdo you know a joke\b",
    r"\bmake me laugh\b",
    r"\bsay something funny\b",
    r"\btell me something funny\b",
]


JOKE_REACTION_PATTERNS = [
    r"\bthat is not very nice\b",
    r"\bthat's not very nice\b",
    r"\bnot very nice\b",
    r"\bthat's rude\b",
    r"\bthat is rude\b",
    r"\bnot nice\b",
]


INSURANCE_PATTERNS = [
    r"\bclaim\b",
    r"\baccident\b",
    r"\bpolicy\b",
    r"\binsurance\b",
    r"\bdamage\b",
    r"\bcar\b",
    r"\bvehicle\b",
    r"\bcollision\b",
    r"\bcrash\b",
    r"\bincident\b",
    r"\breport\b",
]


def _matches(
    message: str,
    patterns: list[str],
) -> bool:
    return any(
        re.search(
            pattern,
            message,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


def classify_conversation_intent(
    message: str,
) -> ConversationIntent:

    normalized = message.strip().lower()

    if not normalized:
        return "unknown"

    # Joke reactions must be checked before generic
    # conversation routing.
    if _matches(
        normalized,
        JOKE_REACTION_PATTERNS,
    ):
        return "joke_reaction"

    if _matches(
        normalized,
        JOKE_PATTERNS,
    ):
        return "joke"

    # Insurance context takes priority for mixed messages.
    if _matches(
        normalized,
        INSURANCE_PATTERNS,
    ):
        return "insurance_claim"

    if _matches(
        normalized,
        GOODBYE_PATTERNS,
    ):
        return "goodbye"

    if _matches(
        normalized,
        THANKS_PATTERNS,
    ):
        return "thanks"

    if _matches(
        normalized,
        GREETING_PATTERNS,
    ):
        return "greeting"

    return "unrelated"
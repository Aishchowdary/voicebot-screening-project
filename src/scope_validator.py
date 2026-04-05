"""
scope_validator.py
Validates bot responses and user queries against the selected scenario scope.
Prevents out-of-scope information from leaking into responses.
"""

import logging
import re
from typing import Literal, Optional

logger = logging.getLogger(__name__)

Scenario = Literal["presale", "sales", "marketing"]


# ---------------------------------------------------------------------------
# Keyword / phrase lists per scenario
# ---------------------------------------------------------------------------

OUT_OF_SCOPE_PATTERNS: dict[str, list[str]] = {
    "presale": [
        # Pricing / commercial
        r"\bpric(e|ing|ed)\b",
        r"\bcost(s|ing)?\b",
        r"\bdiscount\b",
        r"\bquot(e|ation)\b",
        r"\bbudget\b",
        r"\bfee\b",
        r"\binvoice\b",
        r"\bpayment\b",
        r"\bsubscription\b",
        # Sales closure
        r"\border\b",
        r"\bpurchase\b",
        r"\bbuy\b",
        r"\bsign.?up\b",
        r"\bcontract\b",
        r"\bagreement\b",
        r"\bnegotiat\b",
        # Competitor commentary
        r"\bcompetitor\b",
        r"\bvs\.?\s",
        r"\bversus\b",
        r"\bbetter than\b",
        r"\bworse than\b",
        # Implementation commitment
        r"\bimplementation timeline\b",
        r"\bgo.?live\b",
        r"\bdeployment date\b",
    ],
    "sales": [
        r"\bpric(e|ing|ed)\b",
        r"\bcost(s|ing)?\b",
        r"\bpayment term\b",
        r"\binvoice\b",
        r"\bprocess.*(order|invoice)\b",
        r"\blegal\b",
        r"\bcompliance\b",
        r"\bcustom development\b",
        r"\bnegotiat\b",
    ],
    "marketing": [
        r"\bpric(e|ing|ed)\b",
        r"\bcost(s|ing)?\b",
        r"\bconfidential\b",
        r"\boverride.*(policy|terms)\b",
        r"\bbind(ing)?\b",
        r"\bpersonali[sz]ed recommendation\b",
    ],
}

# Redirect responses keyed by language
REDIRECT_RESPONSES: dict[str, dict[str, str]] = {
    "presale": {
        "en": (
            "That's a great question! However, pricing and commercial details are best "
            "discussed directly with our sales team who can tailor a proposal specifically "
            "for your needs. What I can do is help you understand our capabilities and "
            "schedule a call with the right person. Would that work for you?"
        ),
        "hi": (
            "Bahut accha sawaal hai! Lekin pricing aur commercial details ke baare mein "
            "hamare sales team aapko zyada sahi tarike se bata payenge. Main aapke liye "
            "unke saath ek meeting schedule kar sakta hoon. Kya yeh theek rahega?"
        ),
    },
    "sales": {
        "en": (
            "I appreciate the question. That topic falls outside what I'm able to assist "
            "with directly, but our team can address it. Shall I connect you?"
        ),
        "hi": (
            "Yeh sawaal hamare sales team ke liye zyada suitable hai. Kya main aapko unse "
            "milwa sakta hoon?"
        ),
    },
    "marketing": {
        "en": (
            "Great curiosity! That specific detail is best handled by our dedicated team. "
            "Would you like me to arrange a conversation with them?"
        ),
        "hi": (
            "Yeh jankari hamare dedicated team se lena behtar hoga. Kya main unse "
            "baat karwa sakta hoon?"
        ),
    },
}


class ScopeValidator:
    """
    Validates whether a piece of text is within the allowed scope
    for the selected scenario, and provides redirect responses when it is not.
    """

    def __init__(self, scenario: Scenario = "presale") -> None:
        self.scenario = scenario
        self._patterns = [
            re.compile(p, re.IGNORECASE)
            for p in OUT_OF_SCOPE_PATTERNS.get(scenario, [])
        ]
        logger.info(
            "ScopeValidator initialised | scenario=%s | patterns=%d",
            scenario,
            len(self._patterns),
        )

    def is_in_scope(self, text: str) -> bool:
        """Return True if text does NOT contain out-of-scope content."""
        for pattern in self._patterns:
            if pattern.search(text):
                logger.warning(
                    "Out-of-scope pattern matched: '%s' in text: '%s'",
                    pattern.pattern,
                    text[:100],
                )
                return False
        return True

    def get_redirect_response(self, language: str = "en") -> str:
        """Return an appropriate redirect message for the scenario and language."""
        lang_key = language if language in ("en", "hi") else "en"
        responses = REDIRECT_RESPONSES.get(self.scenario, {})
        return responses.get(lang_key, responses.get("en", "I'm sorry, that topic is outside my scope. Let me connect you with the right team."))

    def validate_and_redirect(
        self, text: str, language: str = "en"
    ) -> Optional[str]:
        """
        If *text* is out of scope, return a redirect response.
        If it's in scope, return None.
        """
        if not self.is_in_scope(text):
            return self.get_redirect_response(language)
        return None

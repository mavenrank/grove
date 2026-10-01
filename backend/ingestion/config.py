"""Ingestion configuration: classification rules and scope.

Material outside the two active buckets is extracted and preserved but marked
`deferred` — it never enters a release without an explicit product decision
(handoff §10 'Future buckets', §22 'must not be silently reversed').
"""
from __future__ import annotations

import re

ACTIVE_BUCKETS = ("quant", "logic")

# (skill_id, status, [regexes against deck title]) — first match wins.
# Order matters: specific patterns before generic ones.
CLASSIFICATION_RULES: list[tuple[str, str, list[re.Pattern]]] = [
    # --- Algorithms first: DP/series-adjacent titles that are NOT aptitude ---
    ("other.algorithms", "deferred", [
        re.compile(r"subsequence|longest\s*common|\blcs\b|huffman|dynamic\s*programming|"
                   r"memoization|knapsack|levenshtein|binary\s*search|time\s*complexity|"
                   r"strobogrammatic|palindrome|fibonacci|linked\s*list|binary\s*tree|"
                   r"anagram|roman\s*to|integer\s*to\s*roman|two\s*sum|reverse\s*integer", re.I),
    ]),
    # --- Quantitative: numbers (crypt arithmetic is Numbers per standard syllabi) ---
    ("quant.numbers.crypt_arithmetic", "active", [re.compile(r"crypt\s*arith", re.I)]),
    ("quant.numbers.power_cycles", "active", [re.compile(r"power\s*cycle|remainder\s*cycle", re.I)]),
    ("quant.numbers.factors_multiples", "active", [re.compile(r"factors?\s*(and|&)?\s*multiples", re.I)]),
    ("quant.numbers.hcf_lcm", "active", [re.compile(r"hcf|lcm|greatest\s*common", re.I)]),
    ("quant.numbers.arithmetic", "active", [
        # Numeric roots precede the generic painted-cube/dice rule (#5).
        # Bare "Cubes" remains reasoning; multi-topic content review is separate.
        re.compile(r"\b(?:cube|square)[\s-]+roots?\b", re.I),
        re.compile(r"numbers?\s*\d", re.I),
        re.compile(r"\bnumbers\b", re.I),
        re.compile(r"remainder\s*theorem", re.I),
    ]),
    # --- Quantitative: fractions/ratios/percentages ---
    ("quant.frp.percentages", "active", [re.compile(r"percent", re.I)]),
    ("quant.frp.ratios", "active", [re.compile(r"ratio|variation", re.I)]),
    ("quant.frp.fractions", "active", [re.compile(r"fraction", re.I)]),
    # --- Quantitative: averages/mixtures/finance ---
    ("quant.avg.simple_interest", "active", [re.compile(r"simple\s*interest", re.I)]),
    ("quant.avg.compound_interest", "active", [re.compile(r"compound\s*interest|si\s*and\s*ci", re.I)]),
    ("quant.avg.averages", "active", [re.compile(r"average", re.I)]),
    ("quant.avg.mixtures", "active", [re.compile(r"mixture|alligation", re.I)]),
    ("quant.avg.profit_loss", "active", [re.compile(r"profit|loss", re.I)]),
    # --- Quantitative: time/work/speed ---
    ("quant.tws.pipes_cisterns", "active", [re.compile(r"pipes?\b|cistern", re.I)]),
    ("quant.tws.time_work", "active", [re.compile(r"time\s*(and|&)\s*work|work\s*rate|work\s*equiv|division\s*of\s*work", re.I)]),
    ("quant.tws.relative_speed", "active", [re.compile(r"relative\s*speed", re.I)]),
    ("quant.tws.speed_distance_time", "active", [re.compile(r"time\s*speed|speed\b|distance\s*(and|&)?\s*time", re.I)]),
    # --- Quantitative: algebra/data ---
    ("quant.alg.ages", "active", [re.compile(r"problems?\s*on\s*ages|\bages\b", re.I)]),
    ("quant.alg.equations", "active", [re.compile(r"equation", re.I)]),
    ("quant.alg.data_interpretation", "active", [re.compile(r"data\s*interpretation|caselet|data\s*sufficiency", re.I)]),
    # --- Quantitative: misc (clocks/calendars are quant-adjacent staples) ---
    ("quant.misc.clocks", "active", [re.compile(r"\bclocks?\b", re.I)]),
    ("quant.misc.calendars", "active", [re.compile(r"calendars?\b", re.I)]),
    # --- Logic: patterns & sequences ---
    ("logic.pat.number_series", "active", [re.compile(r"\bseries\b|number\s*series", re.I)]),
    ("logic.pat.pattern_completion", "active", [re.compile(r"cubes|dice|pattern\s*completion", re.I)]),
    # --- Logic: syllogisms & relations ---
    ("logic.rel.analogies", "active", [re.compile(r"\banalog(y|ies)\b", re.I)]),
    ("logic.rel.blood_relations", "active", [re.compile(r"blood\s*relation", re.I)]),
    ("logic.rel.directions", "active", [re.compile(r"directions?\b", re.I)]),
    ("logic.rel.syllogisms", "active", [re.compile(r"syllogism", re.I)]),
    # --- Logic: arrangements ---
    ("logic.arr.data_arrangements", "active", [re.compile(r"data\s*arrangement|seating|\bsitting\b|arrangement", re.I)]),
    ("logic.arr.ordering", "active", [re.compile(r"ordering|order\s*and\s*ranking|\branking\b", re.I)]),
    ("logic.arr.grouping", "active", [re.compile(r"\bgrouping\b|\bpuzzles?\b", re.I)]),
    # --- Logic: coding & classification ---
    ("logic.code.coding_decoding", "active", [re.compile(r"coding", re.I)]),
    ("logic.code.classification", "active", [re.compile(r"classification|categorization|odd\s*(one|man)\s*out", re.I)]),
    # --- Logic: statements & inference ---
    ("logic.inf.assumptions", "active", [re.compile(r"assumption", re.I)]),
    ("logic.inf.conclusions", "active", [re.compile(r"conclusion|statement\s*(and|&)\s*conclusion", re.I)]),
    ("logic.inf.arguments", "active", [re.compile(r"cause\s*(and|&)\s*effect|\barguments?\b", re.I)]),
    # --- Verbal (deferred bucket) ---
    ("verbal.vocab.synonyms", "deferred", [re.compile(r"synonym", re.I)]),
    ("verbal.vocab.antonyms", "deferred", [re.compile(r"antonym", re.I)]),
    ("verbal.vocab.analogies", "deferred", [re.compile(r"analogy", re.I)]),
    ("verbal.vocab.homophones", "deferred", [re.compile(r"homophone|homonym|heteronym", re.I)]),
    ("verbal.vocab.spelling", "deferred", [re.compile(r"spelling", re.I)]),
    ("verbal.grammar.prepositions", "deferred", [re.compile(r"preposition", re.I)]),
    ("verbal.grammar.adjectives", "deferred", [re.compile(r"adjectiv|adverb", re.I)]),
    ("verbal.grammar.tenses", "deferred", [re.compile(r"tense|gerund|infinitiv", re.I)]),
    ("verbal.grammar.voice", "deferred", [re.compile(r"voice", re.I)]),
    ("verbal.grammar.speech", "deferred", [re.compile(r"direct\s*(and|&)?\s*indirect|speech", re.I)]),
    ("verbal.grammar.articles", "deferred", [re.compile(r"article|interrogative", re.I)]),
    ("verbal.grammar.word_groups", "deferred", [re.compile(r"word\s*group", re.I)]),
    ("verbal.grammar.sentence_correction", "deferred", [re.compile(r"sentence\s*correction|subject.?verb|parallelism|pronoun.?antecedent|modifiers", re.I)]),
    ("verbal.comprehension.parajumbles", "deferred", [re.compile(r"parajumble", re.I)]),
    ("verbal.comprehension.sentence_completion", "deferred", [re.compile(r"sentence\s*completion", re.I)]),
    ("verbal.comprehension.reading", "deferred", [re.compile(r"reading\s*comprehension", re.I)]),
    ("verbal.comprehension.idioms", "deferred", [re.compile(r"idiom|phrasal", re.I)]),
    ("verbal.comprehension.writing", "deferred", [re.compile(r"writing", re.I)]),
    # --- Deferred / other ---
    ("other.algorithms", "deferred", [re.compile(r"algorithm|sort|heap|tree|graph|sieve|knapsack|subsequence|array|linked|stack|queue|complexity|recursion", re.I)]),
    ("other.java", "deferred", [re.compile(r"java\b|operators|control\s*structure", re.I)]),
    ("other.dbms", "deferred", [re.compile(r"dbms|rdbms", re.I)]),
    ("other.soft_skills", "deferred", [re.compile(r"team\s*working|attention\s*to\s*detail|critical\s*thinking|decision\s*mak|problem\s*solving|orientation", re.I)]),
]

DEFERRED_SKILL = "unclassified.deferred"


def classify_title(title: str) -> tuple[str, str]:
    """Return (skill_id, status) for a deck title. First matching rule wins.

    Underscores, dots, and brackets are treated as separators so that filenames
    like `21-BLOOD_RELATIONS_1-2023-04-19` classify identically to prose titles.
    """
    normalized = title.replace("_", " ").replace(".", " ").replace("(", " ").replace(")", " ")
    for skill_id, status, patterns in CLASSIFICATION_RULES:
        for pat in patterns:
            if pat.search(normalized):
                return skill_id, status
    return DEFERRED_SKILL, "deferred"

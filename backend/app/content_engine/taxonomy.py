"""Grove taxonomy: buckets → topics → skills (handoff §10).

The skill is the unit of learner progress; question families attach to skills.

Alignment notes (v0.2 taxonomy review):
  - Standard aptitude syllabi (placement/competitive-exam lists) place crypt
    arithmetic under Numbers, so it lives there instead of Coding.
  - The corpus carries Analogy, Clocks, and Calendars decks; these map to
    reasoning/quant-misc skills so their teaching content reaches Learn.
  - Statements-and-inference skills are declared so future decks classify
    cleanly; no generator families attach to them yet.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    id: str
    name: str


@dataclass(frozen=True)
class Topic:
    id: str
    name: str
    skills: tuple[Skill, ...]


@dataclass(frozen=True)
class Bucket:
    id: str
    name: str
    topics: tuple[Topic, ...]


QUANT = Bucket(
    id="quant",
    name="Quantitative Reasoning",
    topics=(
        Topic("quant.numbers", "Numbers", (
            Skill("quant.numbers.arithmetic", "Arithmetic and applications"),
            Skill("quant.numbers.crypt_arithmetic", "Crypt arithmetic"),
            Skill("quant.numbers.divisibility", "Divisibility"),
            Skill("quant.numbers.factors_multiples", "Factors and multiples"),
            Skill("quant.numbers.hcf_lcm", "HCF and LCM"),
            Skill("quant.numbers.power_cycles", "Power cycles and remainders"),
        )),
        Topic("quant.fractions_ratios_percentages", "Fractions, ratios, and percentages", (
            Skill("quant.frp.fractions", "Fractions"),
            Skill("quant.frp.ratios", "Ratios"),
            Skill("quant.frp.proportions", "Proportions and variation"),
            Skill("quant.frp.percentages", "Percentages"),
            Skill("quant.frp.percent_change", "Percent change"),
        )),
        Topic("quant.averages_mixtures_finance", "Averages, mixtures, and finance", (
            Skill("quant.avg.averages", "Averages"),
            Skill("quant.avg.mixtures", "Mixtures and alligation"),
            Skill("quant.avg.profit_loss", "Profit and loss"),
            Skill("quant.avg.simple_interest", "Simple interest"),
            Skill("quant.avg.compound_interest", "Compound interest"),
        )),
        Topic("quant.time_work_speed", "Time, work, and speed", (
            Skill("quant.tws.time_work", "Time and work"),
            Skill("quant.tws.pipes_cisterns", "Pipes and cisterns"),
            Skill("quant.tws.speed_distance_time", "Speed, distance, and time"),
            Skill("quant.tws.relative_speed", "Relative speed"),
        )),
        Topic("quant.algebra_data", "Algebra and data", (
            Skill("quant.alg.equations", "Equations"),
            Skill("quant.alg.expressions", "Expressions"),
            Skill("quant.alg.ages", "Problems on ages"),
            Skill("quant.alg.data_interpretation", "Data interpretation"),
        )),
        Topic("quant.misc", "Clocks and calendars", (
            Skill("quant.misc.clocks", "Clocks"),
            Skill("quant.misc.calendars", "Calendars"),
        )),
    ),
)

LOGIC = Bucket(
    id="logic",
    name="Logical and Analytical Reasoning",
    topics=(
        Topic("logic.patterns_sequences", "Patterns and sequences", (
            Skill("logic.pat.number_series", "Number series"),
            Skill("logic.pat.letter_series", "Letter series"),
            Skill("logic.pat.pattern_completion", "Pattern completion (cubes and dice)"),
        )),
        Topic("logic.syllogisms_relations", "Syllogisms and relations", (
            Skill("logic.rel.syllogisms", "Syllogisms"),
            Skill("logic.rel.inequalities", "Inequalities"),
            Skill("logic.rel.blood_relations", "Blood relations"),
            Skill("logic.rel.directions", "Directions"),
            Skill("logic.rel.analogies", "Analogies"),
        )),
        Topic("logic.arrangements", "Arrangements and constraints", (
            Skill("logic.arr.seating", "Seating arrangements"),
            Skill("logic.arr.ordering", "Ordering and ranking"),
            Skill("logic.arr.grouping", "Grouping and puzzles"),
            Skill("logic.arr.data_arrangements", "Data arrangements"),
        )),
        Topic("logic.coding_classification", "Coding and classification", (
            Skill("logic.code.coding_decoding", "Coding-decoding"),
            Skill("logic.code.symbol_substitution", "Symbol substitution"),
            Skill("logic.code.classification", "Classification (odd one out)"),
        )),
        Topic("logic.statements_inference", "Statements and inference", (
            Skill("logic.inf.assumptions", "Assumptions"),
            Skill("logic.inf.conclusions", "Conclusions"),
            Skill("logic.inf.arguments", "Arguments and cause-effect"),
        )),
    ),
)

BUCKETS: tuple[Bucket, ...] = (QUANT, LOGIC)

ALL_SKILLS: dict[str, Skill] = {
    skill.id: skill
    for bucket in BUCKETS
    for topic in bucket.topics
    for skill in topic.skills
}


def topic_of_skill(skill_id: str) -> Topic | None:
    for bucket in BUCKETS:
        for topic in bucket.topics:
            if any(s.id == skill_id for s in topic.skills):
                return topic
    return None


def bucket_of_skill(skill_id: str) -> Bucket | None:
    topic = topic_of_skill(skill_id)
    if topic is None:
        return None
    for bucket in BUCKETS:
        if any(t.id == topic.id for t in bucket.topics):
            return bucket
    return None


def skill_name(skill_id: str) -> str:
    """Human name for a skill id, falling back to the id's last segment."""
    skill = ALL_SKILLS.get(skill_id)
    if skill:
        return skill.name
    return (skill_id.split(".")[-1] if skill_id else skill_id).replace("_", " ").replace("-", " ").title() or skill_id

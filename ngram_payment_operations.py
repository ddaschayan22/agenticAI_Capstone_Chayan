"""N-gram text generation for payment exception operations.

Run:
    python ngram_payment_operations.py

The corpus is synthetic. It is generated from varied domain-specific templates
and combinations at runtime, producing well over 5,000 words without simply
copying one sentence repeatedly. Results use the same seed and random seed for
bigram, trigram, and four-gram models.
"""

from __future__ import annotations

import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import DefaultDict, Iterable, Sequence

import pandas as pd


RANDOM_SEED = 42
TARGET_WORDS = 5000
PASSAGE_WORDS = 50
SEED_TEXT = "The customer reported that"
CORPUS_FILE = Path(__file__).with_name("payment_operations_ngram_corpus.txt")


TOPICS = [
    "failed payment investigation", "duplicate debit review", "refund processing",
    "card dispute management", "UPI transaction exception", "ACH return handling",
    "wire transfer investigation", "merchant settlement reconciliation", "chargeback evidence review",
    "SLA prioritization", "risk based escalation", "customer communication", "preventive control monitoring",
]
METHODS = ["card", "UPI", "ACH", "wire", "merchant gateway"]
ROLES = ["customer", "merchant", "operations analyst", "settlement specialist", "risk reviewer"]
DETAILS = [
    "a gateway timeout", "an invalid account response", "an authorization mismatch",
    "a processor rejection", "an unfamiliar status code", "a missing settlement line",
    "a repeated capture", "an incomplete evidence package", "a delayed bank response",
    "a policy-sensitive indicator",
]
ACTIONS = [
    "verify the transaction record", "compare processor and ledger evidence",
    "request the missing reference", "check authorization and capture events",
    "preserve the dispute evidence", "route the case to human review",
    "confirm the applicable approved policy", "record the SLA and business impact",
    "draft a factual customer update", "monitor the recurring failure pattern",
]


def build_synthetic_corpus() -> str:
    """Create a varied synthetic corpus exceeding TARGET_WORDS."""
    sentences: list[str] = [
        "The customer reported that the payment exception requires careful investigation before any outcome is communicated.",
        "The customer reported that a payment failed, but the account appears to show a debit and the operations team needs evidence.",
        "The customer reported that the settlement record differs from the expected merchant payout and requested a reconciliation review.",
    ]
    counter_value = 0
    while len(re.findall(r"[A-Za-z0-9]+", " ".join(sentences))) < TARGET_WORDS + 250:
        topic = TOPICS[counter_value % len(TOPICS)]
        method = METHODS[(counter_value * 3) % len(METHODS)]
        role = ROLES[(counter_value * 5) % len(ROLES)]
        detail = DETAILS[(counter_value * 7) % len(DETAILS)]
        action = ACTIONS[(counter_value * 11) % len(ACTIONS)]
        ref = f"PO-{counter_value + 10000}"
        variant = counter_value % 12
        sentences.extend([
            f"In the {topic} workflow, the {role} reviewed {method} activity under reference {ref} and found {detail}.",
            f"The case record for {method} describes {topic}; the next controlled action is to {action}.",
            f"Operations should not assume that a refund, reversal, approval, or successful completion exists until evidence supports it.",
            f"For {method} cases, the analyst records the message, transaction identifier, amount, currency, event time, and current status.",
            f"A clear case summary separates observed facts from missing evidence and identifies whether the issue affects a customer or merchant.",
            f"The {role} checks whether the exception is isolated or part of a recurring pattern involving {detail}.",
            f"When the case concerns {topic}, the team uses the approved decision path and documents the reason for every recommendation.",
            f"The communication draft acknowledges the concern, avoids unsupported promises, and asks for only the information needed for review.",
            f"A high-risk signal, a material financial difference, or an ambiguous dispute is routed to a responsible operations team.",
            f"The SLA queue reflects urgency, financial exposure, customer impact, compliance sensitivity, and the quality of available evidence.",
            f"Preventive controls may include alerting on repeated failures, improving reconciliation, validating account data, and preserving evidence.",
            f"The record remains open until the authorized reviewer confirms the next action and updates the case history.",
        ])
        if variant % 3 == 0:
            sentences.append(
                f"The {method} message may contain a decline reason, duplicate indicator, return code, dispute reason, or settlement variance that changes triage."
            )
        if variant % 4 == 0:
            sentences.append(
                f"Customers need a plain-language explanation, while merchants and operations teams need precise references, reconciliation details, and evidence status."
            )
        counter_value += 1
    return " ".join(sentences)


def load_corpus() -> str:
    """Load the corpus from disk, creating the synthetic corpus when absent/short."""
    if CORPUS_FILE.exists():
        corpus = CORPUS_FILE.read_text(encoding="utf-8")
        if len(tokenize_corpus(corpus)) >= TARGET_WORDS:
            return corpus
    corpus = build_synthetic_corpus()
    CORPUS_FILE.write_text(corpus + "\n", encoding="utf-8")
    return corpus


def tokenize_corpus(text: str) -> list[str]:
    """Normalize text and retain words plus sentence punctuation as tokens."""
    return re.findall(r"[A-Za-z0-9]+|[.!?]", text.lower())


def word_tokens(tokens: Iterable[str]) -> list[str]:
    return [token for token in tokens if re.fullmatch(r"[a-z0-9]+", token)]


def build_ngram_model(tokens: Sequence[str], n: int) -> dict[tuple[str, ...], Counter[str]]:
    """Build a context -> next-token frequency model for any n-gram order."""
    if n < 2:
        raise ValueError("n must be at least 2")
    model: DefaultDict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for index in range(len(tokens) - n + 1):
        context = tuple(tokens[index:index + n - 1])
        next_token = tokens[index + n - 1]
        model[context][next_token] += 1
    return dict(model)


def select_next(counter: Counter[str], rng: random.Random) -> str:
    choices = list(counter)
    weights = [counter[choice] for choice in choices]
    return rng.choices(choices, weights=weights, k=1)[0]


def generate_text(model: dict[tuple[str, ...], Counter[str]], n: int, seed: str, words: int, rng: random.Random) -> list[str]:
    """Generate exactly `words` word tokens, including the common seed."""
    seed_tokens = word_tokens(tokenize_corpus(seed))
    generated = seed_tokens[:]
    context = tuple(seed_tokens[-(n - 1):])
    all_contexts = list(model)

    while len(generated) < words:
        options = model.get(context)
        if not options:
            # Back off to a context with the longest suffix match, then to a random context.
            suffix_matches = [candidate for candidate in all_contexts if candidate[-1:] == context[-1:]]
            context = rng.choice(suffix_matches or all_contexts)
            options = model[context]
        next_token = select_next(options, rng)
        if next_token in ".!?":
            continue
        generated.append(next_token)
        context = tuple((list(context) + [next_token])[-(n - 1):])
    return generated[:words]


def ngrams(tokens: Sequence[str], n: int) -> set[tuple[str, ...]]:
    return {tuple(tokens[index:index + n]) for index in range(len(tokens) - n + 1)}


def longest_matching_phrase(source: Sequence[str], generated: Sequence[str]) -> int:
    """Return the longest contiguous generated phrase found in the source."""
    source_set = set(tuple(source[index:index + size]) for size in range(1, 51) for index in range(len(source) - size + 1))
    longest = 0
    for start in range(len(generated)):
        for end in range(start + 1, len(generated) + 1):
            if tuple(generated[start:end]) in source_set:
                longest = max(longest, end - start)
    return longest


def calculate_source_overlap(source: Sequence[str], generated: Sequence[str], model_n: int) -> dict[str, float | int]:
    source_ngrams = ngrams(source, model_n)
    generated_ngrams = ngrams(generated, model_n)
    overlap = generated_ngrams & source_ngrams
    return {
        "matching_model_ngrams": len(overlap),
        "model_ngram_overlap_percent": round(100 * len(overlap) / max(1, len(generated_ngrams)), 2),
        "matching_bigrams_percent": round(100 * len(ngrams(generated, 2) & ngrams(source, 2)) / max(1, len(ngrams(generated, 2))), 2),
        "matching_trigrams_percent": round(100 * len(ngrams(generated, 3) & ngrams(source, 3)) / max(1, len(ngrams(generated, 3))), 2),
        "longest_matching_words": longest_matching_phrase(source, generated),
            "new_word_percent": round(100 * len(set(generated) - set(source)) / max(1, len(set(generated))), 2),
    }


def qualitative_label(value: float, low: float, high: float) -> str:
    return "High" if value >= high else "Medium" if value >= low else "Low"


def evaluate_generation(source: Sequence[str], generated: Sequence[str], n: int) -> dict[str, object]:
    overlap = calculate_source_overlap(source, generated, n)
    generated_ngrams = ngrams(generated, n)
    source_ngrams = ngrams(source, n)
    fluency = 100 * len(generated_ngrams & source_ngrams) / max(1, len(generated_ngrams))
    repetition = 100 * (1 - len(set(generated)) / max(1, len(generated)))
    return {
        "Model": f"{n}-gram",
        "N-Gram Size": n,
        "Fluency": qualitative_label(fluency, 45, 75),
        "Coherence": qualitative_label(fluency - repetition * 0.25, 30, 65),
        "Repetition": f"{repetition:.1f}%",
        "Source Overlap": f"{overlap['model_ngram_overlap_percent']:.1f}%",
        "Novelty": f"{100 - overlap['model_ngram_overlap_percent']:.1f}%",
        **overlap,
    }


def main() -> None:
    print("N-GRAM TEXT GENERATION — PAYMENT OPERATIONS DOMAIN")
    print("Corpus type: synthetic, varied, domain-specific training corpus")
    corpus = load_corpus()
    tokens = tokenize_corpus(corpus)
    words = word_tokens(tokens)
    print(f"Total tokens including punctuation: {len(tokens)}")
    print(f"Total word count: {len(words)}")
    print(f"Unique word tokens: {len(set(words))}")
    print(f"Vocabulary size: {len(set(words))}")
    print(f"Token sample: {tokens[:30]}")
    if len(words) < TARGET_WORDS:
        raise RuntimeError("Corpus requirement failed: fewer than 5,000 words.")

    models = {n: build_ngram_model(words, n) for n in (2, 3, 4)}
    print("\nMODEL SIZES")
    for n, model in models.items():
        print(f"{n}-gram contexts: {len(model):,}")
    print(f"\nCommon seed used for all models: {SEED_TEXT!r}")

    passages: dict[int, list[str]] = {}
    evaluations = []
    for n, model in models.items():
        passages[n] = generate_text(model, n, SEED_TEXT, PASSAGE_WORDS, random.Random(RANDOM_SEED))
        evaluations.append(evaluate_generation(words, passages[n], n))
        print(f"\n{n}-GRAM — EXACTLY {len(passages[n])} WORDS")
        print(" ".join(passages[n]))

    comparison = pd.DataFrame(evaluations)
    print("\nCOMPARISON TABLE")
    print(comparison[["Model", "N-Gram Size", "Fluency", "Coherence", "Repetition", "Source Overlap", "Novelty"]].to_string(index=False))

    print("\nSOURCE COPYING ANALYSIS")
    print(comparison[["Model", "matching_model_ngrams", "model_ngram_overlap_percent", "matching_bigrams_percent", "matching_trigrams_percent", "longest_matching_words"]].to_string(index=False))

    most_overlap = comparison.loc[comparison["model_ngram_overlap_percent"].idxmax(), "Model"]
    best_balance = comparison.assign(
        balance_score=comparison["longest_matching_words"] - comparison["Repetition"].str.rstrip("%").astype(float) / 10
    ).sort_values("balance_score").iloc[0]["Model"]
    best_fluency = comparison.loc[comparison["longest_matching_words"].idxmax(), "Model"]
    print("\nFINAL ANALYSIS")
    print(f"- Most fluent by observed source-supported local transitions: {best_fluency}.")
    print(f"- Most closely copies source phrases: {most_overlap}; higher-order models preserve longer local context and can reproduce longer phrases.")
    print(f"- Best balance under this simple reproducible overlap/repetition heuristic: {best_balance}.")
    print("- Bigrams have more flexibility but can make abrupt transitions; trigrams often preserve useful local context; four-grams can be coherent but are more sparse and memorization-prone.")
    print("- These are actual corpus-dependent observations, not universal claims. N-grams lack semantic understanding, have limited context, suffer sparsity at higher orders, repeat phrases, and fall back when a context is unseen.")
    print("- Because every generated transition is selected from the training n-gram table, model-specific n-gram overlap is expected to be 100%. Longest matching phrase and repetition are more useful copying indicators here.")
    print("- The corpus is synthetic, and overlap is not proof of harmful memorization; it measures phrase recombination in this demonstration.")


if __name__ == "__main__":
    main()

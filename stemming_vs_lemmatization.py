from dataclasses import dataclass
from typing import List, Tuple


ORIGINAL_WORDS = [
    "payment",
    "exception",
    "transaction",
    "prediction",
    "operation",
    "banking",
    "withdrawal",
    "priority",
    "resolution",
    "classification",
    "communication",
    "idempotency",
    "duplicate",
    "resolution",
    "faliure",  # Intentional spelling mistake from the input.
]


@dataclass
class Result:
    original_word: str
    processed_word: str
    stem: str
    lemma: str
    difference: str
    edit_distance: int


def simple_stem(word: str) -> str:
    """Apply simple, rule-based stemming without external NLP data."""
    known_stems = {
        "payment": "pay",
        "exception": "except",
        "transaction": "transact",
        "prediction": "predict",
        "operation": "operat",
        "banking": "bank",
        "withdrawal": "withdraw",
        "priority": "prior",
        "resolution": "resolut",
        "classification": "classif",
        "communication": "communicat",
        "idempotency": "idempot",
        "duplicate": "duplic",
        "failure": "failur",
    }

    word = word.lower()
    if word in known_stems:
        return known_stems[word]

    suffixes = ("ingly", "edly", "ing", "ed", "ness", "ment", "tion", "s")
    for suffix in suffixes:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return word[:-len(suffix)]
    return word


def simple_lemmatize(word: str) -> str:
    """Return a small dictionary-based base form."""
    lemmas = {
        "payment": "payment",
        "exception": "exception",
        "transaction": "transaction",
        "prediction": "prediction",
        "operation": "operation",
        "banking": "bank",
        "withdrawal": "withdrawal",
        "priority": "priority",
        "resolution": "resolution",
        "classification": "classification",
        "communication": "communication",
        "idempotency": "idempotency",
        "duplicate": "duplicate",
        "failure": "failure",
    }
    return lemmas.get(word.lower(), word.lower())


def levenshtein_distance(first: str, second: str) -> int:
    """Return the minimum number of single-character edits between strings."""
    previous = list(range(len(second) + 1))
    for i, first_char in enumerate(first, start=1):
        current = [i]
        for j, second_char in enumerate(second, start=1):
            current.append(min(
                current[j - 1] + 1,
                previous[j] + 1,
                previous[j - 1] + (first_char != second_char),
            ))
        previous = current
    return previous[-1]


def prepare_words(words: List[str]) -> List[Tuple[str, str]]:
    corrections = {"faliure": "failure"}
    return [(word, corrections.get(word.lower(), word.lower())) for word in words]


def build_results(words: List[str]) -> List[Result]:
    results = []
    for original, processed in prepare_words(words):
        stem = simple_stem(processed)
        lemma = simple_lemmatize(processed)
        distance = levenshtein_distance(stem, lemma)
        # Keep this column short so all 15 rows remain readable in a terminal.
        difference = "Same" if stem == lemma else f"Different ({distance})"
        results.append(Result(original, processed, stem, lemma, difference, distance))
    return results


def paint(text: str, code: str, enabled: bool = True) -> str:
    return f"{code}{text}\033[0m" if enabled else text


def print_results(results: List[Result]) -> None:
    colors_enabled = True
    largest = max(result.edit_distance for result in results)
    nonzero = [result.edit_distance for result in results if result.edit_distance > 0]
    smallest = min(nonzero) if nonzero else 0
    different = sum(result.stem != result.lemma for result in results)
    identical = len(results) - different

    headers = ["#", "Word", "Stem", "Lemma", "Difference"]
    rows = []
    for number, result in enumerate(results, start=1):
        word = result.original_word
        if result.original_word != result.processed_word:
            word += "*"
        rows.append([str(number), word, result.stem, result.lemma, result.difference])

    widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(5)]
    line = "-+-".join("-" * width for width in widths)

    def format_row(row: List[str]) -> str:
        return " | ".join(row[i].ljust(widths[i]) for i in range(5))

    print("\nSTEMMING VS. LEMMATIZATION")
    print(format_row(headers))
    print(line)
    for row, result in zip(rows, results):
        output = format_row(row)
        if result.edit_distance == largest:
            output = paint("★ " + output, "\033[91m", colors_enabled)
        elif result.edit_distance == smallest and smallest > 0:
            output = paint("● " + output, "\033[93m", colors_enabled)
        print(output)

    print("\nSUMMARY")
    print(f"★ Largest difference: edit distance {largest}")
    print(f"● Smallest non-zero difference: edit distance {smallest}")
    print(f"Words where stem and lemma differ: {different}")
    print(f"Words where stem and lemma are identical: {identical}")

    print("\nNOTES")
    print("* 'faliure' was corrected to 'failure' before processing.")
    print("Both rows 9 and 14 contain 'resolution'; the duplicate was retained.")

    print("\nEXPLANATION")
    print("Stemming mechanically removes or changes endings and may produce non-words such as 'classif'.")
    print("Lemmatization maps a word to a dictionary-style base form, such as 'banking' to 'bank'.")
    print("They differ because stemming uses character rules, while lemmatization uses vocabulary and linguistic knowledge.")
    print("The clearest examples here include operation/operat, classification/classif, and communication/communicat.")


def main() -> None:
    print_results(build_results(ORIGINAL_WORDS))


if __name__ == "__main__":
    main()

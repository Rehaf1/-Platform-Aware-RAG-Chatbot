"""
Pulls a small, memory-light subset of HotpotQA (English) and TyDi QA (Arabic +
English) using streaming mode -- never downloads the full datasets, only
fetches the N examples we actually keep.

Both datasets provide their own small context passages per question (not
"search all of Wikipedia"), so each example is tiny -- a handful of short
paragraphs plus a question and gold answer.
"""

import json
from datasets import load_dataset

N_HOTPOT = 50        # how many HotpotQA questions to pull (English only)
N_TYDI_EN = 50        # TyDi QA questions to pull, English
N_TYDI_AR = 100       # TyDi QA questions to pull, Arabic
# English total = N_HOTPOT + N_TYDI_EN = 100
# Arabic total  = N_TYDI_AR                = 100
# Grand total = 200, English/Arabic balanced 100/100


def extract_hotpotqa(n=N_HOTPOT):
    print(f"Streaming HotpotQA, taking first {n} examples...")
    ds = load_dataset(
        "hotpotqa/hotpot_qa",
        "default",
        split="validation",
        streaming=True,
        revision="refs/convert/parquet",
    )

    examples = []
    for i, row in enumerate(ds):
        if i == 0:
            print("First row keys:", list(row.keys()))

        if i >= n:
            break

        # row["context"] is {"title": [...], "sentences": [[...], [...]]}
        # flatten each title's sentences into one paragraph
        titles = row["context"]["title"]
        sentence_lists = row["context"]["sentences"]
        passages = [
            {"title": t, "text": " ".join(sents)}
            for t, sents in zip(titles, sentence_lists)
        ]

        examples.append({
            "id": row["id"],
            "question": row["question"],
            "gold_answer": row["answer"],
            "language": "en",
            "passages": passages,
        })

    return examples


def extract_tydiqa(counts_wanted):
    """counts_wanted: dict like {'english': 50, 'arabic': 100}"""
    print(f"Streaming TyDi QA, target counts: {counts_wanted}...")
    ds = load_dataset("google-research-datasets/tydiqa", "secondary_task", split="validation", streaming=True)

    counts = {lang: 0 for lang in counts_wanted}
    examples = []

    for row in ds:
        # TyDi QA ids are prefixed with the language, e.g. "arabic-1234-..."
        row_lang = row["id"].split("-")[0].lower()
        if row_lang not in counts_wanted:
            continue
        if counts[row_lang] >= counts_wanted[row_lang]:
            if all(counts[l] >= counts_wanted[l] for l in counts_wanted):
                break
            continue

        answers = row["answers"]["text"]
        gold_answer = answers[0] if answers else ""

        examples.append({
            "id": row["id"],
            "question": row["question"],
            "gold_answer": gold_answer,
            "language": "ar" if row_lang == "arabic" else "en",
            "passages": [{"title": row.get("title", ""), "text": row["context"]}],
        })
        counts[row_lang] += 1

    print("Actual counts pulled:", counts)
    return examples


if __name__ == "__main__":
    hotpot = extract_hotpotqa(N_HOTPOT)
    tydi = extract_tydiqa({"english": N_TYDI_EN, "arabic": N_TYDI_AR})

    all_examples = {
        "hotpotqa_en": hotpot,
        "tydiqa": tydi,
    }

    n_en = len(hotpot) + sum(1 for e in tydi if e["language"] == "en")
    n_ar = sum(1 for e in tydi if e["language"] == "ar")

    with open("benchmark_subset.json", "w", encoding="utf-8") as f:
        json.dump(all_examples, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(hotpot)} HotpotQA + {len(tydi)} TyDi QA = {len(hotpot) + len(tydi)} total")
    print(f"English: {n_en}  |  Arabic: {n_ar}")
    print("Output: benchmark_subset.json")
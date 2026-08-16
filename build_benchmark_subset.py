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

N_HOTPOT = 30       # how many HotpotQA questions to pull
N_TYDI_PER_LANG = 20  # how many TyDi QA questions to pull, per language


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


def extract_tydiqa(n_per_lang=N_TYDI_PER_LANG, languages=("english", "arabic")):
    print(f"Streaming TyDi QA, taking first {n_per_lang} examples per language {languages}...")
    ds = load_dataset("google-research-datasets/tydiqa", "secondary_task", split="validation", streaming=True)

    counts = {lang: 0 for lang in languages}
    examples = []

    for row in ds:
        # TyDi QA ids are prefixed with the language, e.g. "arabic-1234-..."
        row_lang = row["id"].split("-")[0].lower()
        if row_lang not in languages:
            continue
        if counts[row_lang] >= n_per_lang:
            if all(c >= n_per_lang for c in counts.values()):
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

    return examples


if __name__ == "__main__":
    hotpot = extract_hotpotqa()
    tydi = extract_tydiqa()

    all_examples = {
        "hotpotqa_en": hotpot,
        "tydiqa": tydi,
    }

    with open("benchmark_subset.json", "w", encoding="utf-8") as f:
        json.dump(all_examples, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(hotpot)} HotpotQA examples and {len(tydi)} TyDi QA examples")
    print("Output: benchmark_subset.json")
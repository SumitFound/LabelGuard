"""Run labeled image sets through LabelGuard's image pipeline and rule engine."""
import csv
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.engine import evaluate, load_rules
from app.pipeline import process_image

CLASSES = ["PASS", "FAIL", "NEEDS_REVIEW"]


def read_labels(folder):
    path = folder / "labels.csv"
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return {row["filename"]: row["expected_verdict"].strip().upper()
                for row in csv.DictReader(stream)
                if row.get("filename") and row.get("expected_verdict")}


def main():
    image_suffixes = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
    datasets = [ROOT / "sample_images", ROOT / "eval_data"]
    rows, timings, errors = [], [], []
    for folder in datasets:
        if not folder.is_dir():
            continue
        labels = read_labels(folder)
        for image_path in sorted(p for p in folder.iterdir() if p.suffix.lower() in image_suffixes):
            expected = labels.get(image_path.name)
            started = time.perf_counter()
            try:
                processed, detections, barcode, _ = process_image(image_path.read_bytes())
                text = "\n".join(item[0] for item in detections)
                if not text.strip():
                    raise ValueError("No readable text found")
                result = evaluate(text, [{"text": t, "bbox": box, "conf": conf} for t, box, conf in detections],
                                  image_width_px=processed.shape[1], barcode=barcode)
                actual = result["verdict"]
                rows.append({"filename": image_path.name, "expected": expected, "actual": actual, "results": result["results"]})
            except Exception as exc:
                actual = "NEEDS_REVIEW"
                rows.append({"filename": image_path.name, "expected": expected, "actual": actual, "results": []})
                errors.append(f"{image_path.name}: {type(exc).__name__}: {exc}")
            finally:
                timings.append(time.perf_counter() - started)

    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    rules = load_rules()
    per_rule = {rule["id"]: Counter() for rule in rules}
    for row in rows:
        for result in row["results"]:
            per_rule[result["id"]][result["status"]] += 1
    labeled_rows = [row for row in rows if row["expected"] in CLASSES]
    correct = sum(row["expected"] == row["actual"] for row in labeled_rows)
    accuracy = correct / len(labeled_rows) if labeled_rows else 0.0
    avg_seconds = sum(timings) / len(timings) if timings else 0.0
    matrix = [[sum(r["expected"] == expected and r["actual"] == predicted for r in labeled_rows)
               for predicted in CLASSES] for expected in CLASSES]

    lines = ["# Evaluation metrics", "",
             f"- Images processed: {len(rows)}",
             f"- Labeled images evaluated: {len(labeled_rows)}",
             f"- Accuracy (exact verdict match): {accuracy:.1%} ({correct}/{len(labeled_rows)})" if labeled_rows else "- Accuracy: N/A (no labeled images)",
             f"- Average processing time: {avg_seconds:.3f} seconds per image", "",
             "## Per-rule outcomes", "", "| Rule | Pass | Fail | Needs review |", "|---|---:|---:|---:|"]
    for rule in rules:
        counts = per_rule[rule["id"]]
        lines.append(f"| {rule['id']} | {counts['PASS']} | {counts['FAIL']} | {counts['NEEDS_REVIEW']} |")
    lines += ["", "## Confusion matrix", "", "Rows are expected verdicts; columns are predicted verdicts.", "",
              "| Expected \\ Predicted | PASS | FAIL | NEEDS_REVIEW |", "|---|---:|---:|---:|"]
    for label, values in zip(CLASSES, matrix):
        lines.append(f"| {label} | " + " | ".join(map(str, values)) + " |")
    unlabeled = sum(row["expected"] not in CLASSES for row in rows)
    lines += ["", f"- Files without usable labels: {unlabeled}", f"- Processing errors: {len(errors)}"]
    if errors:
        lines += ["", "## Processing notes", ""] + [f"- {item.replace('|', '/')}" for item in errors]
    (out / "metrics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 5))
    image = ax.imshow(matrix, cmap="Greens")
    ax.set(xticks=range(len(CLASSES)), xticklabels=CLASSES, yticks=range(len(CLASSES)), yticklabels=CLASSES,
           xlabel="Predicted verdict", ylabel="Expected verdict", title="LabelGuard confusion matrix")
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            ax.text(j, i, str(value), ha="center", va="center", color="#18392a")
    fig.colorbar(image, ax=ax, label="Images")
    fig.tight_layout()
    fig.savefig(out / "confusion.png", dpi=160)
    plt.close(fig)
    print(f"Processed {len(rows)} images; evaluated {len(labeled_rows)} labeled images; accuracy={accuracy:.1%}; avg={avg_seconds:.3f}s/image; errors={len(errors)}")


if __name__ == "__main__":
    main()

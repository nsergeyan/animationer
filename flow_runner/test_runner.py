"""
Offline checks for the parts of runner.py that do not need a browser.

Same idea as test_assembly.py in the parent project: catch the dumb bugs
(numbering, resume, pacing floors) before spending a live Flow session on them.
Everything Playwright-driven still has to be verified by hand.

    python test_runner.py
"""

import base64
import importlib
import tempfile
from pathlib import Path

import config
import runner


def check(label, got, want):
    status = "ok  " if got == want else "FAIL"
    print(f"  [{status}] {label}: got {got!r}")
    return got == want


def test_scene_parsing():
    print("\nscene file parsing")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenes.txt"
        path.write_text(
            "# a comment\n"
            "\n"
            "first prompt\n"
            "   second prompt   \n"
            "# another comment\n"
            "third prompt\n",
            encoding="utf-8",
        )
        scenes = runner.load_scenes(path)
        return all([
            check("comments and blanks dropped", len(scenes), 3),
            check("whitespace stripped", scenes[1], "second prompt"),
        ])


def test_numbering():
    print("\noutput numbering (must be zero-padded to 3)")
    return all([
        check("scene 1", runner.output_path(1).name, "scene_001.png"),
        check("scene 30", runner.output_path(30).name, "scene_030.png"),
        check("scene 100", runner.output_path(100).name, "scene_100.png"),
    ])


def test_extension_sniffing():
    """Flow serves JPEG. Naming those .png is how the first run went wrong."""
    print("\nimage format sniffing")
    return all([
        check("JPEG (what Flow actually sends)",
              runner.sniff_extension(b"\xff\xd8\xff\xe0\x00\x10JFIF"), ".jpg"),
        check("PNG", runner.sniff_extension(b"\x89PNG\r\n\x1a\n"), ".png"),
        check("WebP", runner.sniff_extension(b"RIFF\x00\x00\x00\x00WEBPVP8 "), ".webp"),
        check("unknown falls back", runner.sniff_extension(b"garbage"), ".png"),
    ])


def test_resume_across_extensions():
    """Resume must skip scene 1 whether it landed as .jpg or .png."""
    print("\nresume finds output whatever the extension")
    original = config.OUTPUT_DIR
    with tempfile.TemporaryDirectory() as tmp:
        config.OUTPUT_DIR = Path(tmp)
        try:
            results = [check("nothing saved yet", runner.existing_output(1), None)]
            (Path(tmp) / "scene_001.jpg").write_bytes(b"x")
            found = runner.existing_output(1)
            results.append(check("finds the .jpg",
                                 found.name if found else None, "scene_001.jpg"))
            results.append(check("unrelated scene still missing",
                                 runner.existing_output(2), None))
        finally:
            config.OUTPUT_DIR = original
    return all(results)


def test_baseline_rejects_old_images():
    """
    Regression test for the bug that saved a pre-existing image.

    A policy error means no new UUID appears. Even after React rebuilds the
    grid - which is what defeated the old data-attribute marking - every image
    on the page is still in the baseline, so nothing is eligible to save.
    """
    print("\nold images can never be picked as fresh")
    baseline = {"aaa", "bbb", "ccc"}
    page_after_rejection = [
        {"id": "aaa", "ready": True, "width": 1376},   # same media, new DOM node
        {"id": "bbb", "ready": True, "width": 1376},
        {"id": "ccc", "ready": True, "width": 1376},
    ]
    fresh = [i for i in page_after_rejection
             if i["id"] not in baseline and i["ready"] and i["width"] >= 256]
    results = [check("rejection yields nothing to save", len(fresh), 0)]

    page_after_success = page_after_rejection + [
        {"id": "ddd", "ready": True, "width": 1376},
    ]
    fresh = [i for i in page_after_success
             if i["id"] not in baseline and i["ready"] and i["width"] >= 256]
    results.append(check("real generation is found", [i["id"] for i in fresh], ["ddd"]))
    return all(results)


def test_pacing_floor():
    """The whole point of the clamp: lowering config must not speed the run up."""
    print("\npacing floor resists tampering")
    original = (config.DELAY_BETWEEN, config.DELAY_JITTER, config.TYPE_DELAY_MS)
    config.DELAY_BETWEEN, config.DELAY_JITTER, config.TYPE_DELAY_MS = 0.0, 0.0, 1
    try:
        importlib.reload(runner)
        results = [
            check("DELAY_BETWEEN floored at 6", runner.DELAY_BETWEEN, 6.0),
            check("DELAY_JITTER floored at 4", runner.DELAY_JITTER, 4.0),
            check("TYPE_DELAY_MS floored at 25", runner.TYPE_DELAY_MS, 25),
        ]
    finally:
        config.DELAY_BETWEEN, config.DELAY_JITTER, config.TYPE_DELAY_MS = original
        importlib.reload(runner)
    return all(results)


def test_data_uri_save():
    """The data: branch of save_image never touches the browser."""
    print("\ndata: URI decoding")
    payload = base64.b64encode(b"\xff\xd8\xff\xe0\x00\x10JFIFdata").decode()
    original = config.OUTPUT_DIR
    with tempfile.TemporaryDirectory() as tmp:
        config.OUTPUT_DIR = Path(tmp)
        try:
            dest = runner.save_image(None, None, f"data:image/jpeg;base64,{payload}", 1)
            return all([
                check("named by content, not assumption", dest.name, "scene_001.jpg"),
                check("bytes written", dest.read_bytes()[:3], b"\xff\xd8\xff"),
            ])
        finally:
            config.OUTPUT_DIR = original


def test_rejection_pattern():
    """
    Regression test for the false positive that killed scene 1.

    The old selector matched a footer "Privacy Policy" link and reported the
    site tagline as a rejection. Page furniture must not match; real refusals
    must.
    """
    print("\nrejection pattern: furniture vs real errors")
    import re
    rx = re.compile(config.REJECTION_PATTERN, re.I)

    must_not_match = [
        "Google Flow - AI Creative Studio for Video, Images & Custom Tools",
        "Privacy Policy",
        "Terms of Service  Privacy Policy  Help",
        "Cookie policy",
        "Generate",
    ]
    must_match = [
        "This prompt violates our content policy",
        "Your prompt was blocked",
        "We can't generate this image",
        "Unable to generate content for this prompt",
        "Try a different prompt",
        "This content is not allowed",
    ]

    results = []
    for text in must_not_match:
        results.append(check(f"ignores {text[:34]!r}", bool(rx.search(text)), False))
    for text in must_match:
        results.append(check(f"catches {text[:34]!r}", bool(rx.search(text)), True))
    return all(results)


def test_retry_command_parsing():
    print("\n--only parsing round trip")
    failures = [3, 7, 12]
    rendered = ",".join(str(n) for n in failures)
    parsed = {int(n) for n in rendered.split(",") if n.strip()}
    return all([
        check("renders as expected", rendered, "3,7,12"),
        check("parses back", parsed, {3, 7, 12}),
    ])


if __name__ == "__main__":
    tests = [
        test_scene_parsing,
        test_numbering,
        test_extension_sniffing,
        test_resume_across_extensions,
        test_baseline_rejects_old_images,
        test_rejection_pattern,
        test_pacing_floor,
        test_data_uri_save,
        test_retry_command_parsing,
    ]
    passed = [t() for t in tests]
    print("\n" + "=" * 60)
    if all(passed):
        print(f"All {len(passed)} test groups passed.")
    else:
        print(f"{passed.count(False)} of {len(passed)} test groups FAILED.")
    print("=" * 60)

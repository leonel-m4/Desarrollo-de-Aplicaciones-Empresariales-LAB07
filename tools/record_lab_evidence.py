"""Record real lab outputs without implementing the student's manual answers."""
import argparse
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "entregable" / "evidencias"


def save_json(name, data):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / name).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def run_command(name, args, expected_code=0):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    result = subprocess.run(
        [sys.executable, "manage.py", *args], cwd=ROOT, env=env,
        capture_output=True, text=True, encoding="utf-8", check=False,
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    command = " ".join(["python", "manage.py", *args])
    text = (
        f"Command: {command}\nExit code: {result.returncode}\n\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    (OUTPUT / name).write_text(text.rstrip() + "\n", encoding="utf-8")
    if result.returncode != expected_code:
        raise RuntimeError(f"{command}: unexpected exit code {result.returncode}")
    return result.stdout


def snapshot():
    import django
    from django.db import connection
    from django.test import Client
    from django.test.utils import CaptureQueriesContext
    from django.urls import reverse

    from blog.models import Author, Comment, Post

    with CaptureQueriesContext(connection) as captured:
        response = Client().get(reverse("front_page"))
    sql = [query["sql"] for query in captured]
    return {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "django": django.get_version(),
        "dataset": {
            "authors": Author.objects.count(),
            "posts": Post.objects.count(),
            "comments": Comment.objects.count(),
            "published_posts": Post.objects.filter(published=True).count(),
        },
        "front_page": {
            "url": reverse("front_page"), "status": response.status_code,
            "queries": len(sql),
            "separate_author_queries": sum('FROM "blog_author"' in q for q in sql),
            "tag_queries": sum('FROM "blog_tag"' in q for q in sql),
            "sql": sql,
        },
    }


def answer_evidence(source):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    from blog.duel.questions import QUESTIONS
    from blog.duel.runner import SOURCES, run_question

    module = importlib.import_module(SOURCES[source])
    evidence = []
    for question in QUESTIONS:
        with CaptureQueriesContext(connection) as captured:
            verdict = run_question(question, getattr(module, question.key))
        evidence.append({
            "question": question.key, "status": verdict.status,
            "queries": verdict.queries, "detail": verdict.detail,
            "expected": question.expected,
            "sql": [query["sql"] for query in captured],
        })
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage", choices=("baseline", "team", "optimized"), required=True,
    )
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()

    if args.stage == "baseline":
        data = snapshot()
        if data["front_page"]["queries"] != 23:
            raise RuntimeError("Record the baseline before optimizing, using the fixed seed.")
        save_json("portada_antes.json", data)
        save_json("comparacion_ia.json", answer_evidence("ai"))
        run_command("conteos_shell.txt", ["shell", "-c", (
            "from blog.models import Author, Post, Comment\n"
            "print({'authors': Author.objects.count(), "
            "'posts': Post.objects.count(), 'comments': Comment.objects.count()})"
        )])
        run_command("duel_ia.txt", ["duel", "--source", "ai"])
        run_command(
            "test_portada_antes.txt",
            ["test", "blog.tests.test_front_page", "--verbosity", "2", "--noinput"],
            expected_code=1,
        )
    elif args.stage == "team":
        save_json("consultas_equipo.json", answer_evidence("team"))
        run_command("duel_equipo.txt", ["duel"])
        run_command(
            "test_consultas_equipo.txt",
            ["test", "blog.tests.test_duel", "blog.tests.test_integration", "--noinput"],
        )
    else:
        data = snapshot()
        if data["front_page"]["queries"] != 2:
            raise RuntimeError("The optimized front page must execute two queries.")
        save_json("portada_despues.json", data)
        run_command(
            "test_portada_despues.txt",
            ["test", "blog.tests.test_front_page", "--verbosity", "2", "--noinput"],
        )
        run_command("suite_completa.txt", ["test", "--verbosity", "2", "--noinput"])
    print(f"Recorded {args.stage} evidence in entregable/evidencias/.")


if __name__ == "__main__":
    main()

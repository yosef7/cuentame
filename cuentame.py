"""Cuéntame: a local, source-grounded family memory interview."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "gemma4:e2b"
MAX_QUESTIONS = 8


def markdown_text(value: str) -> str:
    """Keep the speaker's words literal inside a Markdown block quote."""
    return "\n".join("> " + line for line in value.splitlines())


def safe_filename(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")
    return f"recuerdo-{slug or 'persona'}.md"


def build_question_prompt(name: str, exchanges: list[tuple[str, str]]) -> str:
    history = "\n".join(
        f"Pregunta {i}: {question}\nRespuesta {i}: {answer}"
        for i, (question, answer) in enumerate(exchanges, 1)
    )
    return (
        "Eres una entrevistadora respetuosa que ayuda a conservar recuerdos familiares. "
        "Haz UNA pregunta abierta, corta y concreta en español sobre un recuerdo de "
        f"{name}. No inventes hechos, no imites a esa persona, no sugieras respuestas, "
        "no repitas preguntas anteriores. Pregunta por una comida, canción, frase, lugar "
        "o pequeña historia. Devuelve únicamente la pregunta, sin prefacio.\n"
        f"Entrevista hasta ahora:\n{history or '(sin respuestas todavía)'}"
    )


def ask_question(name: str, exchanges: list[tuple[str, str]], model: str) -> str:
    payload = json.dumps(
        {
            "model": model,
            "prompt": build_question_prompt(name, exchanges),
            "stream": False,
            "think": False,
            "options": {"temperature": 0.4, "num_predict": 90},
        }
    ).encode("utf-8")
    request = Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=90) as response:
            result = json.load(response)
    except (URLError, HTTPError, TimeoutError, OSError) as exc:
        raise RuntimeError(
            "No se pudo consultar Ollama en 127.0.0.1:11434. "
            "Inicia Ollama y descarga el modelo indicado."
        ) from exc
    question = str(result.get("response", "")).strip().strip('"“”')
    if not question or "\n" in question or len(question) > 240 or not question.endswith("?"):
        raise RuntimeError("El modelo no devolvió una sola pregunta válida; no se guardó nada.")
    return question


def render_memory(name: str, exchanges: list[tuple[str, str]]) -> str:
    if not exchanges:
        raise ValueError("Se necesita al menos una respuesta.")
    lines = [
        f"# Recuerdos de {name}",
        "",
        f"Entrevista registrada el {date.today().isoformat()}.",
        "",
        "Estas son las respuestas originales de quien contó la historia. "
        "Las preguntas fueron propuestas por un modelo local; ninguna respuesta fue escrita por él.",
        "",
    ]
    for index, (question, answer) in enumerate(exchanges, 1):
        lines.extend([f"## {index}. {question}", "", markdown_text(answer), ""])
    lines.extend(
        ["---", "", "Lo que no se respondió queda abierto. Revisar este archivo antes de compartirlo.", ""]
    )
    return "\n".join(lines)


def interview(name: str, model: str, count: int) -> list[tuple[str, str]]:
    exchanges: list[tuple[str, str]] = []
    for _ in range(count):
        question = ask_question(name, exchanges, model)
        print(f"\n{question}")
        answer = input("> ").strip()
        if not answer:
            print("Respuesta vacía: se termina sin agregar datos.")
            break
        exchanges.append((question, answer))
        if len(exchanges) >= 6 and input("¿Otra pregunta? [s/N] ").strip().lower() != "s":
            break
    return exchanges


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Entrevista local para conservar recuerdos")
    parser.add_argument("--nombre", help="Nombre de la persona recordada")
    parser.add_argument("--modelo", default=DEFAULT_MODEL)
    parser.add_argument("--preguntas", type=int, default=6)
    parser.add_argument("--salida", type=Path, default=Path("recuerdos"))
    parser.add_argument("--ejemplo", action="store_true", help="Solo muestra un ejemplo ficticio, sin llamar a Ollama")
    args = parser.parse_args(argv)
    if not 1 <= args.preguntas <= MAX_QUESTIONS:
        parser.error(f"--preguntas debe estar entre 1 y {MAX_QUESTIONS}")
    name = "Elena (ficticia)" if args.ejemplo else (args.nombre or input("¿A quién quieres recordar? ").strip())
    if not name:
        parser.error("Indica un nombre")
    if args.ejemplo:
        exchanges = [
            ("¿Qué comida te recuerda a Elena?", "Hacía arroz con coco los domingos."),
            ("¿Qué lugar recuerdas junto a ella?", "La cocina de la casa, con la ventana abierta."),
        ]
    else:
        try:
            exchanges = interview(name, args.modelo, args.preguntas)
        except RuntimeError as exc:
            print(exc, file=sys.stderr)
            return 1
    if not exchanges:
        print("No hay respuestas para guardar.", file=sys.stderr)
        return 1
    args.salida.mkdir(parents=True, exist_ok=True)
    target = args.salida / safe_filename(name)
    if target.exists():
        print(f"El archivo ya existe: {target}", file=sys.stderr)
        return 1
    target.write_text(render_memory(name, exchanges), encoding="utf-8")
    print(f"Guardado en {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import json
import os

from .api import APIServer
from .backup import create_backup, restore_backup
from .cartridge import CharacterOrigin
from .engine import FrankensteinEngine
from .doctor import run_doctor
from .evaluation import run_acceptance, sample_origin
from .renderer import DeterministicRenderer, OllamaRenderer
from .semantic import DeterministicInterpreter, OllamaSemanticInterpreter
from .runtime import HeartbeatPolicy, HeartbeatRunner
from .types import WorldEvent


def _renderer(args):
    if getattr(args, "ollama_model", None):
        return OllamaRenderer(args.ollama_model, base_url=getattr(args, "ollama_url", "http://127.0.0.1:11434"))
    return DeterministicRenderer()


def _interpreter(args):
    semantic_model = getattr(args, "semantic_model", None)
    if semantic_model:
        return OllamaSemanticInterpreter(semantic_model, base_url=getattr(args, "ollama_url", "http://127.0.0.1:11434"))
    if getattr(args, "deterministic_semantic", False):
        return DeterministicInterpreter()
    return None


def _add_model_args(parser):
    parser.add_argument("--ollama-model")
    parser.add_argument("--semantic-model")
    parser.add_argument("--deterministic-semantic", action="store_true")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")


def main(argv=None):
    p = ArgumentParser(prog="frankenstein", description="Persistent renderer-neutral character runtime")
    sub = p.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init")
    init.add_argument("home")
    init.add_argument("--origin")
    init.add_argument("--sample", action="store_true")

    status = sub.add_parser("status")
    status.add_argument("home")

    chat = sub.add_parser("chat")
    chat.add_argument("home")
    chat.add_argument("actor")
    chat.add_argument("text")
    _add_model_args(chat)

    shell = sub.add_parser("shell")
    shell.add_argument("home")
    shell.add_argument("actor")
    _add_model_args(shell)

    observe = sub.add_parser("observe")
    observe.add_argument("home")
    observe.add_argument("summary")
    observe.add_argument("--actor")
    observe.add_argument("--tag", action="append", default=[])

    rebuild = sub.add_parser("rebuild")
    rebuild.add_argument("home")

    verify = sub.add_parser("verify")
    verify.add_argument("home")

    doctor = sub.add_parser("doctor")
    doctor.add_argument("home")

    backup = sub.add_parser("backup")
    backup.add_argument("home")
    backup.add_argument("target")

    restore = sub.add_parser("restore")
    restore.add_argument("archive")
    restore.add_argument("home")

    serve = sub.add_parser("serve")
    serve.add_argument("home")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--token-env", default="FRANKENSTEIN_SERVER_TOKEN")
    _add_model_args(serve)

    heartbeat = sub.add_parser("heartbeat")
    heartbeat.add_argument("home")
    heartbeat.add_argument("--interval-seconds", type=float, default=1800.0)
    heartbeat.add_argument("--cycles", type=int, default=1)

    sub.add_parser("eval")

    args = p.parse_args(argv)
    if args.cmd == "init":
        if args.sample:
            origin = sample_origin()
        elif args.origin:
            origin = CharacterOrigin.load(args.origin)
        else:
            raise SystemExit("init requires --origin FILE or --sample")
        engine = FrankensteinEngine(args.home, origin)
        print(json.dumps(engine.status(), indent=2))
    elif args.cmd == "status":
        print(json.dumps(FrankensteinEngine.open(args.home).status(), indent=2))
    elif args.cmd == "chat":
        engine = FrankensteinEngine.open(args.home, renderer=_renderer(args), interpreter=_interpreter(args))
        print(engine.chat(args.actor, args.text))
    elif args.cmd == "shell":
        engine = FrankensteinEngine.open(args.home, renderer=_renderer(args), interpreter=_interpreter(args))
        print(f"{engine.origin.display_name} is ready. Type /quit to exit.")
        while True:
            try:
                line = input(f"{args.actor}> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line:
                continue
            if line in {"/quit", "/exit"}:
                break
            if line == "/status":
                print(json.dumps(engine.status(), indent=2))
                continue
            print(f"{engine.origin.display_name}> {engine.chat(args.actor, line)}")
    elif args.cmd == "observe":
        engine = FrankensteinEngine.open(args.home)
        event = engine.observe(WorldEvent(args.summary, actor_id=args.actor, tags=tuple(args.tag)))
        print(event.event_id)
    elif args.cmd == "rebuild":
        engine = FrankensteinEngine.open(args.home)
        print(engine.rebuild())
    elif args.cmd == "verify":
        engine = FrankensteinEngine.open(args.home)
        report = engine.store.verify_integrity()
        print(json.dumps({"ok": report.ok, "checked_events": report.checked_events, "errors": report.errors}, indent=2))
        raise SystemExit(0 if report.ok else 2)
    elif args.cmd == "doctor":
        report = run_doctor(FrankensteinEngine.open(args.home))
        print(json.dumps({"ok": report.ok, "checks": report.checks, "details": report.details}, indent=2))
        raise SystemExit(0 if report.ok else 2)
    elif args.cmd == "backup":
        print(create_backup(FrankensteinEngine.open(args.home), args.target))
    elif args.cmd == "restore":
        engine = restore_backup(args.archive, args.home)
        print(json.dumps(engine.status(), indent=2))
    elif args.cmd == "serve":
        engine = FrankensteinEngine.open(args.home, renderer=_renderer(args), interpreter=_interpreter(args))
        token = os.environ.get(args.token_env)
        server = APIServer(engine, args.host, args.port, token=token)
        print(f"serving on http://{args.host}:{args.port}")
        server.serve_forever()
    elif args.cmd == "heartbeat":
        engine = FrankensteinEngine.open(args.home)
        runner = HeartbeatRunner(engine, HeartbeatPolicy(interval_seconds=args.interval_seconds, max_cycles=args.cycles))
        print(f"completed {runner.run()} heartbeat cycle(s)")
    elif args.cmd == "eval":
        passed = run_acceptance()
        print(f"PASS {len(passed)} acceptance probes")
        for name in passed:
            print(name)

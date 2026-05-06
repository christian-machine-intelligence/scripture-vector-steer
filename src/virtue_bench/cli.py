"""
Unified CLI entry point for VirtueBench V2.

Subcommands:
  run       — Run an experiment (from args or YAML config)
  analyze   — Analyze results with statistical tests
  migrate   — Migrate V1 scenarios to V2 format
"""

from __future__ import annotations

import argparse
import asyncio
import faulthandler
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .core.constants import VIRTUES, VARIANTS
from .core.psalms import PSALM_SETS, load_psalm_text, list_psalm_sets
from .core.bible import BOOK_SETS, load_bible_text, list_book_sets
from .core.schema import ExperimentConfig, RunResult
from .steering.corpora import SCRIPTURE_TARGETS
from .stats.bootstrap import aggregate_runs
from .analysis.tables import print_comparison_table, print_aggregated_table, print_variant_grid
from .artifacts.results import write_results, load_results


RUNNER_CHOICES = ["openai-api", "anthropic-api", "claude-cli", "pi-cli", "inspect", "hf-local"]
# Keep CLI artifacts in the repo-local results directory so console logs, status
# files, and result payloads all land in one place.
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"

ICONOCLAST_CONDITION_PROFILES = {
    "all": [
        "control",
        "psalm_baseline",
        "virtue_steer",
        "christian_steer",
        "combined",
        "null_control",
        "christian_null_control",
        "length_control",
    ],
    "steer_only": [
        "control",
        "virtue_steer",
        "christian_steer",
        "null_control",
        "christian_null_control",
    ],
    "scripture_compare": [
        "control",
        "virtue_steer",
        "scripture_steer",
        "null_control",
        "scripture_null_control",
    ],
    "scripture_only_compare": [
        "control",
        "scripture_steer",
        "scripture_null_control",
    ],
    "reasoning_primary": [
        "control",
        "virtue_steer",
        "scripture_steer",
    ],
    "psalm_reasoning_primary": [
        "control",
        "scripture_steer",
    ],
    "scripture_reasoning_primary": [
        "control",
        "scripture_steer",
    ],
    "scripturevec35": [
        "control",
        "scripture_steer",
        "scripture_negative_alpha",
        "scripture_null_control",
    ],
    "reasoning_compare": [
        "control",
        "virtue_steer",
        "scripture_steer",
        "null_control",
        "scripture_null_control",
    ],
    "christian_compare": [
        "control",
        "virtue_steer",
        "christian_steer",
        "null_control",
        "christian_null_control",
    ],
    "prompt_only": [
        "control",
        "psalm_baseline",
        "length_control",
    ],
    "prompt_heavy": [
        "control",
        "psalm_baseline",
        "combined",
        "length_control",
    ],
}


class _TeeTextIO:
    """Mirror console output to both the terminal and a file."""

    def __init__(self, *streams):
        self._streams = streams
        self.encoding = getattr(streams[0], "encoding", "utf-8")
        self.errors = getattr(streams[0], "errors", "strict")

    def write(self, data: str) -> int:
        for stream in self._streams:
            stream.write(data)
        return len(data)

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()

    def isatty(self) -> bool:
        return any(getattr(stream, "isatty", lambda: False)() for stream in self._streams)


@contextmanager
def _iconoclast_console_capture(output_prefix: str):
    """Persist Iconoclast console output even if the shell wrapper is fragile."""
    log_path = RESULTS_DIR / f"{output_prefix}_console.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    console_mode = os.environ.get("VIRTUE_BENCH_ICONOCLAST_CONSOLE", "mirror").strip().lower()
    mirror_stdout = console_mode != "file"

    previous_stdout = sys.stdout
    previous_stderr = sys.stderr
    with open(log_path, "w", encoding="utf-8", buffering=1) as log_file:
        if mirror_stdout:
            sys.stdout = _TeeTextIO(previous_stdout, log_file)
            sys.stderr = _TeeTextIO(previous_stderr, log_file)
        else:
            sys.stdout = log_file
            sys.stderr = log_file
        faulthandler_enabled = False
        try:
            try:
                faulthandler.enable(log_file, all_threads=True)
                faulthandler_enabled = True
            except Exception:
                pass
            print(f"[iconoclast] console log: {log_path}")
            yield log_path
        finally:
            if faulthandler_enabled:
                try:
                    faulthandler.disable()
                except Exception:
                    pass
            sys.stdout.flush()
            sys.stderr.flush()
            sys.stdout = previous_stdout
            sys.stderr = previous_stderr


def _default_iconoclast_output_prefix() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"experiments/iconoclast/iconoclast_{timestamp}"


def _resolve_iconoclast_conditions(args: argparse.Namespace) -> list[str]:
    if args.conditions:
        return list(args.conditions)
    return list(ICONOCLAST_CONDITION_PROFILES[args.condition_profile])


def _parse_named_scale_overrides(raw_values: list[str] | None, *, flag_name: str) -> dict[str, float]:
    overrides: dict[str, float] = {}
    for raw_value in raw_values or []:
        if "=" not in raw_value:
            raise SystemExit(f"{flag_name} expects values like name=1.5")
        name, scale_text = raw_value.split("=", 1)
        name = name.strip()
        scale_text = scale_text.strip()
        if not name or not scale_text:
            raise SystemExit(f"{flag_name} expects values like name=1.5")
        try:
            overrides[name] = float(scale_text)
        except ValueError as exc:
            raise SystemExit(f"{flag_name} expects a numeric scale, got: {raw_value}") from exc
    return overrides


def cmd_run(args: argparse.Namespace) -> None:
    """Run an experiment."""
    from .eval.experiment import run_experiment
    from .runners import RUNNERS, OpenAIAPIRunner, AnthropicAPIRunner, ClaudeCLIRunner, PiCLIRunner

    if args.config:
        with open(args.config) as f:
            config_data = yaml.safe_load(f)
        config = ExperimentConfig(**config_data)
    else:
        config = ExperimentConfig(
            name=args.output or f"experiment_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            model=args.model,
            virtues=VIRTUES if args.subset == "all" else [args.subset],
            variants=VARIANTS if args.variant == "all" else [args.variant],
            runs=args.runs,
            temperature=args.temperature,
            frame="default",
            seed=args.seed,
            limit=args.limit,
            injection_file=args.inject,
            concurrency=args.concurrency,
            retries=args.retries,
            timeout=args.timeout,
            detailed=args.detailed,
        )

    if args.quick:
        config.limit = 10

    # Handle psalm injection (overrides --inject if both specified)
    psalm_set_names = getattr(args, "psalm_set", None)
    psalm_nums = getattr(args, "psalm_numbers", None)
    psalm_random = getattr(args, "psalm_random", None)

    if psalm_set_names or psalm_nums or psalm_random:
        parsed_nums = None
        if psalm_nums:
            parsed_nums = [int(n.strip()) for n in psalm_nums.split(",")]

        from .core.psalms import load_psalm_text
        import tempfile
        psalm_text = load_psalm_text(
            psalm_sets=psalm_set_names,
            psalm_numbers=parsed_nums,
            random_n=psalm_random,
            seed=config.seed,
        )
        # Write to temp file for injection
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8",
        )
        tmp.write(psalm_text)
        tmp.close()
        config.injection_file = tmp.name
        n_psalms = len(psalm_text.split("Psalm ")) - 1
        sets_label = ",".join(psalm_set_names) if psalm_set_names else ""
        print(f"Psalm injection: {n_psalms} psalms ({sets_label or 'custom selection'})")

    # Handle Bible book injection
    bible_books_arg = getattr(args, "bible", None)
    bible_set_arg = getattr(args, "bible_set", None)

    if bible_books_arg or bible_set_arg:
        import tempfile
        bible_text = load_bible_text(
            books=bible_books_arg,
            book_set=bible_set_arg,
        )
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8",
        )
        tmp.write(bible_text)
        tmp.close()
        config.injection_file = tmp.name
        label = bible_set_arg or ",".join(bible_books_arg)
        print(f"Bible injection: {label} (KJV)")

    # Select runner
    # Strip provider prefix (e.g. "openai/gpt-4o" -> "gpt-4o") for SDK/CLI runners
    model_name = config.model.split("/", 1)[-1] if "/" in config.model else config.model

    if args.runner == "openai-api":
        runner = OpenAIAPIRunner(model=model_name)
    elif args.runner == "anthropic-api":
        runner = AnthropicAPIRunner(model=model_name)
    elif args.runner == "claude-cli":
        runner = ClaudeCLIRunner(model=model_name, effort=getattr(args, "effort", "low"))
    elif args.runner == "pi-cli":
        runner = PiCLIRunner(model=model_name)
    elif args.runner == "inspect" and "inspect" in RUNNERS:
        runner = RUNNERS["inspect"](model=config.model)
    elif args.runner == "hf-local":
        from .runners.hf_local import HFLocalRunner
        runner = HFLocalRunner(
            model_name=config.model,
            adapter_path=getattr(args, "hf_adapter", None),
            enable_thinking=getattr(args, "enable_thinking", False),
        )
    else:
        # Auto-detect from model name
        if "claude" in config.model.lower() or "anthropic" in config.model.lower():
            runner = AnthropicAPIRunner(model=model_name)
        else:
            runner = OpenAIAPIRunner(model=model_name)

    print(f"Model: {runner.model_id()}")
    print(f"Runner: {args.runner}")
    print(f"Virtues: {config.virtues}")
    print(f"Variants: {config.variants}")
    print(f"Runs: {config.runs}")
    print(f"Temperature: {config.temperature}")

    print(f"Limit: {config.limit or 'all'}")

    # Set up checkpoint path for incremental saves
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = args.output or f"results_{timestamp}"
    if not filename.endswith(".json"):
        filename += ".json"
    output_path = RESULTS_DIR / filename
    checkpoint_path = output_path.with_name(f"{output_path.stem}_checkpoint.json")

    results = asyncio.run(run_experiment(config, runner, checkpoint_path=checkpoint_path))

    # Clean up checkpoint after successful completion
    if checkpoint_path.exists():
        checkpoint_path.unlink()

    summary_path, logs_path = write_results(results, output_path, write_logs=config.detailed)
    print(f"\nResults saved to: {summary_path}")
    if logs_path:
        print(f"Detailed logs saved to: {logs_path}")

    # Print tables
    print_comparison_table(results)

    if config.runs > 1:
        aggregated = aggregate_runs(results)
        print_aggregated_table(aggregated)
        print_variant_grid(aggregated)


def cmd_analyze(args: argparse.Namespace) -> None:
    """Analyze existing results."""
    from .stats.bootstrap import aggregate_runs
    from .stats.tests import chi_squared_variant
    from .core.schema import RunResult

    path = Path(args.results)
    data = load_results(path)

    # Try to reconstruct RunResults
    results = []
    for d in data:
        try:
            results.append(RunResult(**d))
        except Exception:
            pass

    if not results:
        print("Could not parse results as RunResult objects. Showing raw data.")
        for d in data:
            print(json.dumps(d, indent=2))
        return

    aggregated = aggregate_runs(results)
    print_aggregated_table(aggregated)
    print_variant_grid(aggregated)

    # Chi-squared test across variants
    chi2_result = chi_squared_variant(results)
    print(f"\nChi-squared test across variants:")
    print(f"  chi2 = {chi2_result['chi2']:.4f}, df = {chi2_result['df']}")
    if chi2_result["p_value"] is not None:
        print(f"  p = {chi2_result['p_value']:.6f}")


def cmd_migrate(args: argparse.Namespace) -> None:
    """Migrate V1 scenarios to V2 format."""
    from .migrate import migrate_v1_to_v2
    migrate_v1_to_v2(
        v1_data_dir=Path(args.v1_dir),
        v2_data_dir=Path(args.v2_dir),
    )


def cmd_dashboard(args: argparse.Namespace) -> None:
    """Serve a live dashboard for a specific run prefix."""
    from .dashboard import DashboardConfig, serve_dashboard

    config = DashboardConfig(
        output_prefix=args.output_prefix,
        host=args.host,
        port=args.port,
        refresh_seconds=args.refresh_seconds,
        results_dir=Path(args.results_dir),
        remote_host=args.remote_host,
        remote_user=args.remote_user,
        remote_password_env=args.remote_password_env,
        remote_results_dir=args.remote_results_dir,
    )
    serve_dashboard(config)


def cmd_iconoclast(args: argparse.Namespace) -> None:
    """Run the Iconoclast activation-space steering experiment."""
    from .analysis.iconoclast import (
        print_paired_flip_table,
        print_cross_virtue_matrix,
        print_iconoclast_table,
        write_condition_heatmap,
        write_cross_virtue_heatmap,
    )
    from .steering.experiment import IconoclastConfig, run_iconoclast_experiment
    from .runners.hf_local import HFLocalRunner

    alpha_candidates = None
    if args.alpha_candidates:
        alpha_candidates = [float(value.strip()) for value in args.alpha_candidates.split(",") if value.strip()]
    psalm_family_alpha_scales = _parse_named_scale_overrides(
        getattr(args, "psalm_family_alpha_scale", None),
        flag_name="--psalm-family-alpha-scale",
    )
    psalm_family_lanes = args.psalm_family_lane or []
    if args.include_merged_psalm_family_lane and len(psalm_family_lanes) < 2:
        raise SystemExit(
            "--include-merged-psalm-family-lane requires at least two --psalm-family-lane values"
        )
    if args.sample_offset < 0:
        raise SystemExit("--sample-offset must be non-negative")
    if args.run_index_start < 0:
        raise SystemExit("--run-index-start must be non-negative")
    if args.subspace_rank < 1:
        raise SystemExit("--subspace-rank must be at least 1")

    if args.scripture_targets is not None:
        scripture_targets = list(args.scripture_targets)
    elif psalm_family_lanes:
        scripture_targets = []
    else:
        scripture_targets = ["psalms", "proverbs", "gospels"]

    output_prefix = args.output_prefix or _default_iconoclast_output_prefix()

    config = IconoclastConfig(
        name=output_prefix,
        model=args.model,
        virtues=VIRTUES if args.subset == "all" else [args.subset],
        variants=VARIANTS if args.variant == "all" else [args.variant],
        conditions=_resolve_iconoclast_conditions(args),
        runs=args.runs,
        temperature=args.temperature,
        seed=args.seed,
        limit=10 if args.quick else args.limit,
        detailed=not args.no_logs,
        concurrency=args.concurrency,
        retries=args.retries,
        timeout=args.timeout,
        stage=args.stage,
        cross_matrix=args.cross_matrix,
        pooled_virtue_steer=args.pooled_virtue_steer,
        discernment=args.discernment,
        corpus_path=args.corpus_path,
        external_scripture_corpus_path=args.external_scripture_corpus,
        vector_path=args.vectors,
        extraction_method=args.extraction_method,
        max_length=args.max_length,
        window_radius=args.window_radius,
        window_center=args.window_center,
        alpha_candidates=alpha_candidates or [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0],
        virtue_alpha_scale=args.virtue_alpha_scale,
        christian_alpha_scale=args.christian_alpha_scale,
        scripture_alpha_scale=args.scripture_alpha_scale,
        scripture_runtime_alpha=args.scripture_runtime_alpha,
        subspace_rank=args.subspace_rank,
        psalm_family_alpha_scales=psalm_family_alpha_scales,
        merged_psalm_family_alpha_scale=args.merged_psalm_family_alpha_scale,
        psalm_sets=args.psalm_set or ["random_baseline"],
        psalm_random=args.psalm_random,
        preflight_variant=args.preflight_variant,
        preflight_limit=args.preflight_limit,
        preflight_max_tokens=args.preflight_max_tokens,
        preflight_timeout=args.preflight_timeout,
        preflight_alpha_scale=args.preflight_alpha_scale,
        preflight_max_alpha=args.preflight_max_alpha,
        preflight_policy=args.preflight_policy,
        scripture_targets=scripture_targets,
        psalm_family_lanes=psalm_family_lanes,
        include_merged_psalm_family_lane=args.include_merged_psalm_family_lane,
        psalm_vector_sets=args.psalm_vector_set or [],
        enable_thinking=args.enable_thinking,
        sample_offset=args.sample_offset,
        run_index_start=args.run_index_start,
        output_prefix=output_prefix,
    )

    with _iconoclast_console_capture(config.output_prefix):
        runner = HFLocalRunner(
            model_name=config.model,
            adapter_path=getattr(args, "hf_adapter", None),
            enable_thinking=config.enable_thinking,
        )

        stage_payload = asyncio.run(run_iconoclast_experiment(config, runner))
        print(f"Output prefix: {config.output_prefix}")

        for stage_name in [key for key in stage_payload if key.endswith("_aggregated")]:
            stage = stage_name[:-11]
            aggregated = stage_payload[stage_name]
            results = stage_payload[stage]
            print(f"\n=== Iconoclast summary: {stage} ===")
            print_iconoclast_table(aggregated)
            print_paired_flip_table(results)
            print_cross_virtue_matrix(aggregated)

            output_dir = RESULTS_DIR / "figures"
            for condition_name in (
                "psalm_baseline",
                "length_control",
                "virtue_steer",
                "christian_steer",
                "combined",
                "null_control",
                "christian_null_control",
                "scripture_steer",
                "scripture_null_control",
            ):
                write_condition_heatmap(
                    aggregated,
                    output_dir / f"{config.output_prefix}_{stage}_{condition_name}.png",
                    condition_prefix=condition_name,
                )
            write_cross_virtue_heatmap(
                aggregated,
                output_dir / f"{config.output_prefix}_{stage}_cross_matrix_ratio.png",
                variant="ratio",
                condition_prefix="virtue_steer",
            )


def cmd_analyze_iconoclast(args: argparse.Namespace) -> None:
    """Analyze results from an Iconoclast run."""
    from .analysis.iconoclast import (
        print_paired_flip_table,
        print_cross_virtue_matrix,
        print_iconoclast_table,
        write_condition_heatmap,
        write_cross_virtue_heatmap,
    )

    data = load_results(Path(args.results))
    results = [RunResult(**row) for row in data]
    aggregated = aggregate_runs(results)
    print_iconoclast_table(aggregated)
    print_paired_flip_table(results)
    print_cross_virtue_matrix(aggregated, variant=args.variant)

    if args.write_heatmaps:
        base = Path(args.results).with_suffix("")
        for condition_name in (
            "psalm_baseline",
            "length_control",
            "virtue_steer",
            "christian_steer",
            "combined",
            "null_control",
            "christian_null_control",
            "scripture_steer",
            "scripture_null_control",
        ):
            write_condition_heatmap(
                aggregated,
                base.with_name(f"{base.name}_{condition_name}.png"),
                condition_prefix=condition_name,
            )
        write_cross_virtue_heatmap(
            aggregated,
            base.with_name(f"{base.name}_cross_matrix_{args.variant}.png"),
            variant=args.variant,
            condition_prefix="virtue_steer",
        )


def main():
    parser = argparse.ArgumentParser(
        description="VirtueBench V2: Multi-dimensional virtue evaluation benchmark",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- run ---
    run_parser = subparsers.add_parser("run", help="Run an experiment")
    run_parser.add_argument("--config", type=str, help="YAML config file")
    run_parser.add_argument("--model", default="anthropic/claude-sonnet-4-20250514")
    run_parser.add_argument("--runner", choices=RUNNER_CHOICES, default="inspect")
    run_parser.add_argument("--hf-adapter", type=str, default=None,
                            help="LoRA adapter path for hf-local runner")
    run_parser.add_argument(
        "--enable-thinking",
        action="store_true",
        help="Enable Qwen thinking mode when using the local HF runner",
    )
    run_parser.add_argument("--subset", choices=VIRTUES + ["all"], default="all")
    run_parser.add_argument("--variant", choices=VARIANTS + ["all"], default="all")
    run_parser.add_argument("--runs", type=int, default=5)
    run_parser.add_argument("--temperature", type=float, default=0.7)
    run_parser.add_argument("--seed", type=int, default=42)
    run_parser.add_argument("--limit", type=int, default=None)
    run_parser.add_argument("--quick", action="store_true", help="10 samples per virtue")
    run_parser.add_argument("--inject", type=str, help="Injection text file path")
    run_parser.add_argument("--concurrency", type=int, default=5)
    run_parser.add_argument("--retries", type=int, default=2)
    run_parser.add_argument("--timeout", type=int, default=120)
    run_parser.add_argument("--detailed", action="store_true")
    run_parser.add_argument("--output", type=str, default=None)
    run_parser.add_argument("--effort", choices=["low", "medium", "high", "max"], default="low")
    run_parser.add_argument(
        "--deterministic", action="store_true",
        help="V1-compat: single run at temperature=0",
    )
    # Psalm injection args
    run_parser.add_argument(
        "--psalm-set", action="append", dest="psalm_set",
        choices=list(PSALM_SETS.keys()),
        help="Named psalm subset for injection (can repeat to combine)",
    )
    run_parser.add_argument(
        "--psalm-numbers", type=str, default=None,
        help="Comma-separated psalm numbers for injection (e.g. 23,51,91)",
    )
    run_parser.add_argument(
        "--psalm-random", type=int, default=None,
        help="Inject N randomly-selected psalms",
    )

    # Bible injection args
    run_parser.add_argument(
        "--bible", action="append", dest="bible",
        help="Bible book for injection (e.g., 'Romans', 'MAT:5-7'). Can repeat.",
    )
    run_parser.add_argument(
        "--bible-set", type=str, default=None,
        choices=list(BOOK_SETS.keys()),
        help="Named Bible book collection for injection",
    )

    # --- psalms (list available sets) ---
    psalms_parser = subparsers.add_parser("psalms", help="List available psalm sets")

    # --- bible (list available book sets) ---
    bible_parser = subparsers.add_parser("bible", help="List available Bible book sets")

    # --- analyze ---
    analyze_parser = subparsers.add_parser("analyze", help="Analyze results")
    analyze_parser.add_argument("results", type=str, help="Path to results JSON")

    # --- dashboard ---
    dashboard_parser = subparsers.add_parser(
        "dashboard",
        help="Serve a small GUI for monitoring a run's artifacts",
    )
    dashboard_parser.add_argument(
        "--output-prefix",
        required=True,
        help="Run prefix under results/ (for example experiments/iconoclast/iconoclast_20260420_104500)",
    )
    dashboard_parser.add_argument(
        "--results-dir",
        type=str,
        default=str(RESULTS_DIR),
        help="Local results directory to read from",
    )
    dashboard_parser.add_argument("--host", type=str, default="127.0.0.1")
    dashboard_parser.add_argument("--port", type=int, default=8765)
    dashboard_parser.add_argument(
        "--refresh-seconds",
        type=int,
        default=5,
        help="Browser refresh cadence",
    )
    dashboard_parser.add_argument(
        "--remote-host",
        type=str,
        default=None,
        help="Optional remote host to poll over SSH instead of the local results directory",
    )
    dashboard_parser.add_argument(
        "--remote-user",
        type=str,
        default=None,
        help="Remote SSH user when polling a remote run",
    )
    dashboard_parser.add_argument(
        "--remote-password-env",
        type=str,
        default="VIRTUE_BENCH_REMOTE_PASSWORD",
        help="Environment variable holding the SSH password for remote polling",
    )
    dashboard_parser.add_argument(
        "--remote-results-dir",
        type=str,
        default=None,
        help="Remote results directory (default: C:\\Users\\<user>\\work\\virtue-bench-2\\results)",
    )

    # --- iconoclast ---
    iconoclast_parser = subparsers.add_parser(
        "iconoclast",
        help="Run the Iconoclast activation-space steering experiment",
    )
    iconoclast_parser.add_argument("--model", required=True, help="Open-weight HF model to evaluate")
    iconoclast_parser.add_argument("--hf-adapter", type=str, default=None,
                                   help="Optional PEFT adapter path for the local runner")
    iconoclast_parser.add_argument(
        "--enable-thinking",
        action="store_true",
        help="Enable Qwen thinking mode and score the first visible A/B answer after any <think> block",
    )
    iconoclast_parser.add_argument("--subset", choices=VIRTUES + ["all"], default="all")
    iconoclast_parser.add_argument("--variant", choices=VARIANTS + ["all"], default="all")
    iconoclast_parser.add_argument("--stage", choices=["smoke", "ratio", "full", "all"], default="all")
    iconoclast_parser.add_argument("--runs", type=int, default=10)
    iconoclast_parser.add_argument("--temperature", type=float, default=0.7)
    iconoclast_parser.add_argument("--seed", type=int, default=42)
    iconoclast_parser.add_argument("--limit", type=int, default=None)
    iconoclast_parser.add_argument(
        "--sample-offset",
        type=int,
        default=0,
        help="Skip this many prepared samples before applying --limit; useful for chunked runs",
    )
    iconoclast_parser.add_argument(
        "--run-index-start",
        type=int,
        default=0,
        help="First run index to execute when --runs is a chunk size",
    )
    iconoclast_parser.add_argument("--quick", action="store_true", help="Limit each cell to 10 samples")
    iconoclast_parser.add_argument(
        "--condition-profile",
        choices=sorted(ICONOCLAST_CONDITION_PROFILES),
        default="all",
        help="Preset condition family to run (use steer_only to avoid prompt-related OOM on smaller GPUs)",
    )
    iconoclast_parser.add_argument("--conditions", nargs="+", default=None,
                                   choices=[
                                       "control",
                                       "psalm_baseline",
                                       "virtue_steer",
                                       "christian_steer",
                                       "scripture_steer",
                                       "scripture_negative_alpha",
                                       "combined",
                                       "null_control",
                                       "christian_null_control",
                                       "scripture_null_control",
                                       "length_control",
                                   ])
    iconoclast_parser.add_argument(
        "--scripture-targets",
        nargs="+",
        default=None,
        help=(
            "Scripture-family steering targets to compare when using scripture_steer. "
            f"Built-ins: {', '.join(SCRIPTURE_TARGETS)}. Custom names can be loaded "
            "with --external-scripture-corpus."
        ),
    )
    iconoclast_parser.add_argument(
        "--external-scripture-corpus",
        default=None,
        help="JSONL file containing external Scripture chunks with corpus/target and text fields",
    )
    iconoclast_parser.add_argument(
        "--psalm-family-lane",
        action="append",
        dest="psalm_family_lane",
        choices=list(PSALM_SETS.keys()),
        help="Add a Psalm-family steering lane like trust or wisdom; repeat to compare multiple families",
    )
    iconoclast_parser.add_argument(
        "--include-merged-psalm-family-lane",
        action="store_true",
        help="Also add one merged Psalm lane using the union of the chosen --psalm-family-lane values",
    )
    iconoclast_parser.add_argument(
        "--psalm-vector-set",
        action="append",
        dest="psalm_vector_set",
        choices=list(PSALM_SETS.keys()),
        help="Optional psalm subset(s) to use when extracting the psalm steering vector; default is the whole Psalter",
    )
    iconoclast_parser.add_argument("--cross-matrix", action="store_true",
                                   help="Run each steering vector against each evaluation virtue")
    iconoclast_parser.add_argument(
        "--pooled-virtue-steer",
        action="store_true",
        help="Use one pooled virtue steering vector across all evaluation virtues instead of separate per-virtue vectors",
    )
    iconoclast_parser.add_argument("--discernment", action="store_true",
                                   help="Run optional post-hoc Ignatian discernment prompts")
    iconoclast_parser.add_argument("--corpus-path", type=str, default=None,
                                   help="Override bundled steering corpus path")
    iconoclast_parser.add_argument("--vectors", type=str, default=None,
                                   help="Reuse a precomputed vector artifact (.pt)")
    iconoclast_parser.add_argument(
        "--extraction-method",
        choices=[
            "auto",
            "mean_diff",
            "mean_centered",
            "pca_pairwise",
            "specific_mean_centered",
            "specific_pca_pairwise",
            "scripture_contrast",
            "scripture_subspace_contrast",
            "scripture_other_contrast",
            "scripture_dual_contrast",
            "gospelvec_mean",
        ],
        default="auto",
        help="Vector extraction method to use when building a new artifact",
    )
    iconoclast_parser.add_argument("--max-length", type=int, default=256)
    iconoclast_parser.add_argument("--window-radius", type=int, default=3)
    iconoclast_parser.add_argument(
        "--subspace-rank",
        type=int,
        default=4,
        help="Number of directions to keep for scripture_subspace_contrast extraction",
    )
    iconoclast_parser.add_argument(
        "--window-center",
        type=int,
        default=None,
        help="Optional fixed center layer for the steering window (for GospelVec-style fixed-window comparisons)",
    )
    iconoclast_parser.add_argument("--alpha-candidates", type=str, default=None,
                                   help="Comma-separated alpha grid, e.g. 0.25,0.5,0.75,1.0,1.5,2.0,3.0")
    iconoclast_parser.add_argument(
        "--virtue-alpha-scale",
        type=float,
        default=1.0,
        help="Multiplier applied at benchmark time to virtue steering strength",
    )
    iconoclast_parser.add_argument(
        "--christian-alpha-scale",
        type=float,
        default=1.0,
        help="Multiplier applied at benchmark time to Christian steering strength",
    )
    iconoclast_parser.add_argument(
        "--scripture-alpha-scale",
        type=float,
        default=1.0,
        help="Multiplier applied at benchmark time to scripture-family steering strength",
    )
    iconoclast_parser.add_argument(
        "--scripture-runtime-alpha",
        type=float,
        default=None,
        help="Fixed absolute scripture alpha used at benchmark time, overriding the artifact-tuned alpha",
    )
    iconoclast_parser.add_argument(
        "--psalm-family-alpha-scale",
        action="append",
        default=None,
        metavar="FAMILY=SCALE",
        help="Override scripture alpha scale for one Psalm-family lane, e.g. trust=1.5",
    )
    iconoclast_parser.add_argument(
        "--merged-psalm-family-alpha-scale",
        type=float,
        default=None,
        help="Override scripture alpha scale for the merged Psalm-family lane",
    )
    iconoclast_parser.add_argument(
        "--preflight-variant",
        choices=VARIANTS,
        default="ratio",
        help="Variant to use for the preflight divergence probe",
    )
    iconoclast_parser.add_argument(
        "--preflight-limit",
        type=int,
        default=8,
        help="Samples per virtue for the preflight divergence probe",
    )
    iconoclast_parser.add_argument(
        "--preflight-max-tokens",
        type=int,
        default=32,
        help="Maximum new tokens per sample during the preflight divergence probe",
    )
    iconoclast_parser.add_argument(
        "--preflight-timeout",
        type=int,
        default=45,
        help="Wall-clock timeout per preflight sample, in seconds",
    )
    iconoclast_parser.add_argument(
        "--preflight-alpha-scale",
        type=float,
        default=6.0,
        help="Multiplier applied to the tuned alpha during the preflight divergence probe",
    )
    iconoclast_parser.add_argument(
        "--preflight-max-alpha",
        type=float,
        default=12.0,
        help="Maximum absolute alpha to try when rescuing a zero-divergence preflight path",
    )
    iconoclast_parser.add_argument(
        "--preflight-policy",
        choices=["off", "warn", "skip", "error"],
        default="error",
        help="What to do if the preflight probe finds a zero-divergence steering path",
    )
    iconoclast_parser.add_argument("--psalm-set", action="append", dest="psalm_set",
                                   choices=list(PSALM_SETS.keys()),
                                   help="Psalm set(s) for the prompt-injection baseline")
    iconoclast_parser.add_argument("--psalm-random", type=int, default=None,
                                   help="Add N random psalms to the prompt-injection baseline")
    iconoclast_parser.add_argument("--concurrency", type=int, default=1)
    iconoclast_parser.add_argument("--retries", type=int, default=0)
    iconoclast_parser.add_argument("--timeout", type=int, default=120)
    iconoclast_parser.add_argument("--no-logs", action="store_true",
                                   help="Skip detailed per-sample logs")
    iconoclast_parser.add_argument(
        "--output-prefix",
        type=str,
        default=None,
        help="Result prefix under results/ (default: experiments/iconoclast/iconoclast_<timestamp>)",
    )

    # --- analyze-iconoclast ---
    analyze_iconoclast_parser = subparsers.add_parser(
        "analyze-iconoclast",
        help="Analyze an Iconoclast result file",
    )
    analyze_iconoclast_parser.add_argument("results", type=str, help="Path to results JSON")
    analyze_iconoclast_parser.add_argument("--variant", choices=VARIANTS, default="ratio")
    analyze_iconoclast_parser.add_argument("--write-heatmaps", action="store_true")

    # --- migrate ---
    migrate_parser = subparsers.add_parser("migrate", help="Migrate V1 scenarios to V2 format")
    migrate_parser.add_argument("--v1-dir", required=True, help="Path to V1 data/ directory")
    migrate_parser.add_argument("--v2-dir", required=True, help="Path to V2 data/ directory")

    args = parser.parse_args()

    if args.command == "run":
        if getattr(args, "deterministic", False):
            args.runs = 1
            args.temperature = 0.0
        cmd_run(args)
    elif args.command == "dashboard":
        cmd_dashboard(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "iconoclast":
        cmd_iconoclast(args)
    elif args.command == "analyze-iconoclast":
        cmd_analyze_iconoclast(args)
    elif args.command == "migrate":
        cmd_migrate(args)
    elif args.command == "psalms":
        sets = list_psalm_sets()
        print("\nAvailable psalm sets:\n")
        for name, desc in sets.items():
            psalms = PSALM_SETS[name]["psalms"]
            print(f"  {name:<18} {desc}")
            print(f"  {'':18} Psalms: {','.join(str(p) for p in psalms)}")
            print()
    elif args.command == "bible":
        print("\nAvailable Bible book sets (KJV, all 66 books):\n")
        for name, desc in list_book_sets().items():
            books = BOOK_SETS[name]["books"]
            print(f"  {name:<24} {desc}")
            print(f"  {'':24} Books: {', '.join(books)}")
            print()
        print("Usage:")
        print("  virtue-bench run --bible Romans")
        print("  virtue-bench run --bible 'Matthew 5-7'")
        print("  virtue-bench run --bible-set sermon_on_the_mount")
        print("  virtue-bench run --bible Romans --bible James")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

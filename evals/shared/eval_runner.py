#!/usr/bin/env python3
"""Parallel eval runner for FOTW autoresearch.

Executes all (prompt, run) pairs concurrently via asyncio subprocess,
throttled by a semaphore. Each pair runs: skill invocation → judge scoring → parse.

Outputs JSON to stdout. Streams progress to stderr.
"""

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path


def parse_judge_output(text: str, criteria_count: int) -> list[dict]:
    """Parse judge output into criterion results.

    Matches lines like:
        detection_recall: PASS | reason
        `severity_accuracy`: FAIL | reason
    """
    results = []
    for line in text.splitlines():
        # Strip leading whitespace and backticks
        cleaned = re.sub(r'^[\s`]*', '', line)
        # Strip backticks wrapping criterion IDs
        cleaned = cleaned.replace('`:', ':').replace('`', '')

        m = re.match(r'^([a-z_][a-z_]*): *(PASS|FAIL)', cleaned)
        if m:
            results.append({"cid": m.group(1), "result": m.group(2)})
    return results


async def run_subprocess(cmd: list[str], timeout: int = 120) -> tuple[int, str, str]:
    """Run a subprocess and return (returncode, stdout, stderr)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, stdout.decode(), stderr.decode()
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


async def run_pair(
    sem: asyncio.Semaphore,
    shared_dir: str,
    target_dir: str,
    skill_name: str,
    prompt_file: str,
    prompt_name: str,
    run_num: int,
    model: str,
    judge_model: str,
    fallback_model: str,
    criteria_count: int,
    pair_index: int,
    total_pairs: int,
) -> dict:
    """Run a single (prompt, run) pair: skill → judge → parse."""
    label = f"{prompt_name} run {run_num}"

    async with sem:
        print(f"  [{pair_index}/{total_pairs}] {label}: running skill...", file=sys.stderr, flush=True)

        skill_script = os.path.join(shared_dir, "run-skill-eval.sh")
        judge_script = os.path.join(shared_dir, "score-output.sh")

        # --- Skill invocation ---
        used_fallback = False
        rc, skill_output, _ = await run_subprocess(
            [skill_script, skill_name, prompt_file, model], timeout=180
        )

        if rc != 0 or not skill_output.strip():
            # Try fallback model
            used_fallback = True
            print(f"  [{pair_index}/{total_pairs}] {label}: fallback ({fallback_model})...", file=sys.stderr, flush=True)
            rc, skill_output, _ = await run_subprocess(
                [skill_script, skill_name, prompt_file, fallback_model], timeout=180
            )

        if rc != 0 or not skill_output.strip():
            print(f"  [{pair_index}/{total_pairs}] {label}: SKIP (invocation failed)", file=sys.stderr, flush=True)
            return {
                "prompt": prompt_name,
                "run": run_num,
                "pass": 0,
                "total": 0,
                "criteria": [],
                "status": "skip_invocation",
                "fallback": used_fallback,
            }

        # --- Write skill output to temp file for judge ---
        tmpfile = os.path.join(
            target_dir, f".eval_tmp_{prompt_name}_run{run_num}.txt"
        )
        try:
            Path(tmpfile).write_text(skill_output)

            # --- Judge ---
            print(f"  [{pair_index}/{total_pairs}] {label}: judging...", file=sys.stderr, flush=True)
            rc, judge_output, _ = await run_subprocess(
                [judge_script, target_dir, tmpfile, judge_model], timeout=120
            )

            if rc != 0 or not judge_output.strip():
                print(f"  [{pair_index}/{total_pairs}] {label}: SKIP (judge failed)", file=sys.stderr, flush=True)
                return {
                    "prompt": prompt_name,
                    "run": run_num,
                    "pass": 0,
                    "total": 0,
                    "criteria": [],
                    "status": "skip_judge",
                    "fallback": used_fallback,
                }

            # --- Parse ---
            criteria = parse_judge_output(judge_output, criteria_count)
            pass_count = sum(1 for c in criteria if c["result"] == "PASS")

            fb_tag = " (fallback)" if used_fallback else ""
            print(
                f"  [{pair_index}/{total_pairs}] {label}: {pass_count}/{criteria_count}{fb_tag}",
                file=sys.stderr, flush=True,
            )

            return {
                "prompt": prompt_name,
                "run": run_num,
                "pass": pass_count,
                "total": criteria_count,
                "criteria": criteria,
                "status": "ok",
                "fallback": used_fallback,
            }
        finally:
            # Clean up temp file
            try:
                os.unlink(tmpfile)
            except OSError:
                pass


async def run_eval(args: argparse.Namespace) -> dict:
    """Run all (prompt, run) pairs in parallel."""
    target_dir = args.target_dir
    prompt_dir = os.path.join(target_dir, "prompts")

    # Discover prompts
    prompt_files = sorted(Path(prompt_dir).glob("*.md"))
    if not prompt_files:
        print(f"ERROR: No prompt files in {prompt_dir}", file=sys.stderr)
        sys.exit(1)

    # Count criteria
    criteria_file = os.path.join(target_dir, "criteria.yaml")
    criteria_text = Path(criteria_file).read_text()
    criteria_count = len(re.findall(r'^\s+- id:', criteria_text, re.MULTILINE))
    if criteria_count == 0:
        print(f"ERROR: No criteria found in {criteria_file}", file=sys.stderr)
        sys.exit(1)

    # Build task list
    pairs = []
    pair_index = 0
    for prompt_file in prompt_files:
        prompt_name = prompt_file.stem
        for run_num in range(1, args.runs_per_iteration + 1):
            pair_index += 1
            pairs.append((prompt_file, prompt_name, run_num, pair_index))

    total_pairs = len(pairs)
    print(
        f"=== Parallel eval: {total_pairs} pairs, max_parallel={args.max_parallel} ===",
        file=sys.stderr, flush=True,
    )

    sem = asyncio.Semaphore(args.max_parallel)

    tasks = [
        run_pair(
            sem=sem,
            shared_dir=args.shared_dir,
            target_dir=target_dir,
            skill_name=args.skill_name,
            prompt_file=str(pf),
            prompt_name=pn,
            run_num=rn,
            model=args.model,
            judge_model=args.judge_model,
            fallback_model=args.fallback_model,
            criteria_count=criteria_count,
            pair_index=pi,
            total_pairs=total_pairs,
        )
        for pf, pn, rn, pi in pairs
    ]

    results = await asyncio.gather(*tasks)

    # Aggregate
    total_pass = sum(r["pass"] for r in results)
    total_judgments = sum(r["total"] for r in results)
    criterion_log = []
    for r in results:
        for c in r["criteria"]:
            criterion_log.append(c)

    return {
        "total_pass": total_pass,
        "total_judgments": total_judgments,
        "criterion_log": criterion_log,
        "details": [
            {
                "prompt": r["prompt"],
                "run": r["run"],
                "pass": r["pass"],
                "total": r["total"],
                "status": r["status"],
                "fallback": r["fallback"],
            }
            for r in results
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Parallel eval runner")
    parser.add_argument("--target-dir", required=True, help="Path to target directory")
    parser.add_argument("--skill-name", required=True, help="Skill name")
    parser.add_argument("--model", default="sonnet", help="Skill model")
    parser.add_argument("--judge-model", default="sonnet", help="Judge model")
    parser.add_argument("--fallback-model", default="opus", help="Fallback model")
    parser.add_argument("--runs-per-iteration", type=int, default=3, help="Runs per prompt")
    parser.add_argument("--max-parallel", type=int, default=5, help="Max concurrent pairs")
    parser.add_argument("--shared-dir", required=True, help="Path to evals/shared/")
    args = parser.parse_args()

    result = asyncio.run(run_eval(args))

    # JSON to stdout for eval.sh to consume
    json.dump(result, sys.stdout)
    print()  # trailing newline


if __name__ == "__main__":
    main()

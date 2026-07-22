#!/usr/bin/env bash
set -Eeuo pipefail

# ResolveFlow Codex finite milestone loop.
# Designed for macOS, Linux, or WSL.
# Direct-main workflow: no feature branches, worktrees, PRs, or merges.

MODEL="${MODEL:-gpt-5.6-sol}"
NETWORK_ACCESS="${NETWORK_ACCESS:-true}"
START_AT="${START_AT:-0}"
STOP_AFTER="${STOP_AFTER:-8}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-2}"
RUN_PUBLISH="${RUN_PUBLISH:-0}"
CREATE_BACKUP_TAG="${CREATE_BACKUP_TAG:-1}"
PUSH_STAGE_CHECKPOINTS="${PUSH_STAGE_CHECKPOINTS:-1}"

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 2
  }
}

need git
need codex
need jq
need bash

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "Run this from inside the ResolveFlow Git repository." >&2
  exit 2
}
cd "$ROOT"

if [[ "$(git branch --show-current)" != "main" ]]; then
  echo "Refusing to run: current branch is not main." >&2
  exit 2
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Refusing to start with an unclean working tree." >&2
  git status --short
  exit 2
fi

git pull --ff-only origin main

if [[ "$CREATE_BACKUP_TAG" == "1" ]]; then
  BACKUP_TAG="codex-loop-start-$(date -u +%Y%m%dT%H%M%SZ)"
  git tag -a "$BACKUP_TAG" -m "Before ResolveFlow Codex loop"
  git push origin "$BACKUP_TAG"
  echo "Created backup tag: $BACKUP_TAG"
fi

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_DIR="${CODEX_LOG_DIR:-$HOME/.resolveflow-codex-logs/$RUN_ID}"
mkdir -p "$LOG_DIR"

STAGES=(
  "00-plan|Define the implementation roadmap and acceptance gates|high"
  "01-foundation|Build the shared ResolveFlow foundation|medium"
  "02-retrieval|Add authorized retrieval and rerank controls|medium"
  "03-agent-safety|Add bounded agent and safety controls|high"
  "04-actions-audit|Add approval-gated actions and audit trails|high"
  "05-replay-gate|Add Replay evaluation and release gates|high"
  "06-public-validation|Add public validation and control-room UX|medium"
  "07-final-audit|Complete the final audit and release checks|high"
  "08-publish|Publish the verified snapshot site|medium"
)

check_release_gate() {
  local gate="$ROOT/docs/HUMAN_SIGNOFF.json"
  if [[ ! -f "$gate" ]]; then
    echo "Release gate missing: copy docs/HUMAN_SIGNOFF.example.json to docs/HUMAN_SIGNOFF.json, select a truthful release profile, commit it to main, then resume with START_AT=7." >&2
    return 1
  fi

  jq -e '
    (
      .release_profile == "validated_release" and
      .truth_data.status == "complete" and
      .truth_data.human_authored_truth_count >= 36 and
      .gate_rules_locked == true and
      .held_out_locked == true and
      .practitioner_review.status == "complete" and
      .practitioner_review.reviewer_count >= 3 and
      .practitioner_review.case_count >= 10 and
      (
        (
          .multilingual.status == "validated" and
          .multilingual.fluent_reviewer_confirmed == true
        )
        or
        .multilingual.status == "claim_removed"
      )
    )
    or
    (
      .release_profile == "technical_preview" and
      .technical_preview.operator_authorized == true and
      .technical_preview.limitations_acknowledged == true and
      .technical_preview.publication_allowed == true and
      .technical_preview.human_validation_claimed == false and
      .technical_preview.final_release_verdict_claimed == false and
      .multilingual.status == "claim_removed"
    )
  ' "$gate" >/dev/null
}

run_codex_attempt() {
  local prompt_file="$1"
  local effort="$2"
  local attempt="$3"
  local result_file="$4"
  local events_file="$5"
  local verify_log="$6"

  local extra=""
  if (( attempt > 1 )); then
    extra=$'\n# Repair attempt\nThe independent repository verification command failed after the previous attempt. Preserve the current work, inspect the failure excerpt below, repair the current stage only, rerun relevant checks, and return the required JSON report.\n\n'
    if [[ -f "$verify_log" ]]; then
      extra+="$(tail -n 200 "$verify_log")"
    else
      extra+="The previous attempt did not produce a usable verification log."
    fi
    extra+=$'\n'
  fi

  set +e
  {
    cat "$ROOT/automation/COMMON.md"
    printf '\n'
    cat "$prompt_file"
    printf '%s\n' "$extra"
  } | env -u COHERE_API_KEY \
        GIT_CONFIG_COUNT=1 \
        GIT_CONFIG_KEY_0=remote.origin.pushurl \
        GIT_CONFIG_VALUE_0=disabled://outer-loop-owns-push \
        codex \
          --cd "$ROOT" \
          --ask-for-approval never \
          --sandbox workspace-write \
          --model "$MODEL" \
          -c "model_reasoning_effort=\"$effort\"" \
          -c "sandbox_workspace_write.network_access=$NETWORK_ACCESS" \
          exec \
          --ignore-user-config \
          --json \
          --output-schema "$ROOT/automation/codex-result.schema.json" \
          --output-last-message "$result_file" \
          - | tee "$events_file"
  local rc=${PIPESTATUS[1]}
  set -e
  return "$rc"
}

for i in "${!STAGES[@]}"; do
  if (( i < START_AT || i > STOP_AFTER )); then
    continue
  fi

  IFS='|' read -r stage commit_message effort <<< "${STAGES[$i]}"

  if [[ "$stage" == "08-publish" && "$RUN_PUBLISH" != "1" ]]; then
    echo "Skipping publication stage. Run START_AT=8 RUN_PUBLISH=1 ./automation/run-resolveflow-loop.sh when ready."
    continue
  fi

  if [[ "$stage" == "07-final-audit" || "$stage" == "08-publish" ]]; then
    if ! check_release_gate; then
      echo "Stopped before $stage because neither the validated-release gate nor the truthful technical-preview gate is complete." >&2
      exit 3
    fi
  fi

  prompt_file="$ROOT/automation/prompts/$stage.md"
  [[ -f "$prompt_file" ]] || {
    echo "Missing prompt: $prompt_file" >&2
    exit 2
  }

  echo
  echo "============================================================"
  echo "Stage $i: $stage"
  echo "============================================================"

  if [[ "$(git branch --show-current)" != "main" ]]; then
    echo "Branch changed unexpectedly; refusing to continue." >&2
    exit 4
  fi
  if [[ -n "$(git status --porcelain)" ]]; then
    echo "Working tree is dirty before stage $stage." >&2
    git status --short
    exit 4
  fi

  git pull --ff-only origin main
  start_sha="$(git rev-parse HEAD)"

  stage_passed=0
  result_file="$LOG_DIR/$stage-result.json"
  events_file="$LOG_DIR/$stage-events.jsonl"
  verify_log="$LOG_DIR/$stage-verify.log"

  for ((attempt=1; attempt<=MAX_ATTEMPTS; attempt++)); do
    echo "Codex attempt $attempt/$MAX_ATTEMPTS for $stage"

    if ! run_codex_attempt "$prompt_file" "$effort" "$attempt" "$result_file" "$events_file" "$verify_log"; then
      echo "Codex exited non-zero for $stage attempt $attempt." >&2
      if (( attempt == MAX_ATTEMPTS )); then
        exit 5
      fi
      continue
    fi

    if ! jq -e . "$result_file" >/dev/null 2>&1; then
      echo "Codex did not produce valid structured output: $result_file" >&2
      if (( attempt == MAX_ATTEMPTS )); then
        exit 5
      fi
      continue
    fi

    status="$(jq -r '.status' "$result_file")"
    tests_passed="$(jq -r '.tests_passed' "$result_file")"

    if [[ "$status" == "blocked" ]]; then
      echo "Stage blocked:"
      jq -r '.blockers[]?' "$result_file"
      exit 6
    fi

    if [[ "$status" != "complete" || "$tests_passed" != "true" ]]; then
      echo "Codex reported incomplete or failing work."
      cat "$result_file"
      if (( attempt == MAX_ATTEMPTS )); then
        exit 6
      fi
      continue
    fi

    if [[ "$(git branch --show-current)" != "main" ]]; then
      echo "Codex changed branches; stopping." >&2
      exit 8
    fi

    if [[ "$(git rev-parse HEAD)" != "$start_sha" ]]; then
      echo "Codex committed unexpectedly. The outer loop must own commits and pushes." >&2
      exit 8
    fi

    if [[ "$PUSH_STAGE_CHECKPOINTS" == "1" && -n "$(git status --porcelain)" ]]; then
      git diff --check
      checkpoint_files="$(git status --porcelain | sed -E 's/^.. //')"
      if printf '%s\n' "$checkpoint_files" | grep -E '(^|/)\.env($|\.(local|production|development)$)|\.(pem|p12|pfx|key)$' >/dev/null; then
        echo "Refusing to checkpoint a likely secret-bearing file:" >&2
        printf '%s\n' "$checkpoint_files" | grep -E '(^|/)\.env($|\.(local|production|development)$)|\.(pem|p12|pfx|key)$' >&2
        exit 9
      fi

      git add -A
      git diff --cached --check
      git commit -m "$commit_message (checkpoint)"
      git push origin main
      start_sha="$(git rev-parse HEAD)"
      echo "Checkpoint pushed: $stage @ $(git rev-parse --short HEAD)"
    fi

    if [[ ! -x "$ROOT/scripts/verify.sh" ]]; then
      {
        echo "scripts/verify.sh is missing or not executable."
        echo "The current stage must create or repair the repository verification entry point."
      } | tee "$verify_log"
      if (( attempt == MAX_ATTEMPTS )); then
        exit 7
      fi
      continue
    fi

    set +e
    "$ROOT/scripts/verify.sh" 2>&1 | tee "$verify_log"
    verify_rc=${PIPESTATUS[0]}
    set -e

    if (( verify_rc == 0 )); then
      stage_passed=1
      break
    fi

    echo "Independent verification failed for $stage attempt $attempt." >&2
    if (( attempt == MAX_ATTEMPTS )); then
      exit 7
    fi
  done

  (( stage_passed == 1 )) || {
    echo "Stage did not pass verification: $stage" >&2
    exit 7
  }

  if [[ "$(git branch --show-current)" != "main" ]]; then
    echo "Codex changed branches; stopping." >&2
    exit 8
  fi

  if [[ "$(git rev-parse HEAD)" != "$start_sha" ]]; then
    echo "Codex committed unexpectedly. The outer loop must own commits and pushes." >&2
    exit 8
  fi

  git diff --check

  changed_files="$(git status --porcelain | sed -E 's/^.. //')"
  if printf '%s\n' "$changed_files" | grep -E '(^|/)\.env($|\.(local|production|development)$)|\.(pem|p12|pfx|key)$' >/dev/null; then
    echo "Refusing to commit a likely secret-bearing file:" >&2
    printf '%s\n' "$changed_files" | grep -E '(^|/)\.env($|\.(local|production|development)$)|\.(pem|p12|pfx|key)$' >&2
    exit 9
  fi

  if [[ -z "$(git status --porcelain)" ]]; then
    echo "No repository changes for $stage; treating verified existing state as complete."
  else
    git add -A
    git diff --cached --check
    git commit -m "$commit_message"
  fi

  git push origin main
  git fetch origin main

  if [[ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]]; then
    echo "Local main and origin/main differ after push." >&2
    exit 10
  fi

  echo "$stage $(git rev-parse HEAD)" >> "$LOG_DIR/completed-stages.txt"
  echo "Completed and pushed: $stage @ $(git rev-parse --short HEAD)"
done

echo
echo "Loop finished for requested stage range."
echo "Logs: $LOG_DIR"

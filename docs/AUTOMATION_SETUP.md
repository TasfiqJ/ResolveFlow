# ResolveFlow Codex Loop — setup

This starter uses a finite shell loop over milestone prompt files. It works directly on `main`; it creates no feature branches, worktrees, pull requests, or merges.

## 1. Put this folder in the repository

Copy `automation/` into the root of the checked-out `ResolveFlow` repository.

Copy:

```text
docs/HUMAN_SIGNOFF.example.json
```

to your repository's `docs/` directory as the example only. Do not mark it complete until real humans perform the required work.

Your repository should already contain:

```text
AGENTS.md
docs/CODEX_MASTER_PROMPT_ResolveFlow.md
docs/reference/ResolveFlow_Replay_Master_Plan.pdf
docs/spec/00_ResolveFlow_Replay_Project_Overview_and_Feature_Catalog.md
docs/spec/01_...
...
docs/spec/18_...
```

## 2. Install/check prerequisites

Authenticate Codex first:

```bash
codex
```

Then exit the interactive session.

Check:

```bash
git --version
codex --version
jq --version
bash --version
```

On macOS:

```bash
brew install jq
```

On Ubuntu/WSL:

```bash
sudo apt-get update
sudo apt-get install -y jq
```

## 3. Make the loop executable

```bash
chmod +x automation/run-resolveflow-loop.sh
```

Commit the automation files to `main` before running:

```bash
git switch main
git pull --ff-only origin main
git add automation docs/HUMAN_SIGNOFF.example.json
git commit -m "Add Codex milestone loop"
git push origin main
```

## 4. Run automatic implementation stages 0 through 6

```bash
./automation/run-resolveflow-loop.sh
```

The default run:

- uses `gpt-5.6-sol`;
- runs one stage at a time;
- allows workspace writes and network access;
- withholds `COHERE_API_KEY`;
- runs `scripts/verify.sh` independently;
- makes a direct checkpoint commit to `main` after Codex reports a passing stage, then a smaller completion commit when independent verification produces additional changes;
- pushes `origin/main`;
- stops on failure or blocker;
- stops before the final audit until the human gate is complete;
- skips publication unless explicitly enabled.

## 5. Resume a stopped stage

The script never skips a failure silently.

After repairing the reason for the stop and returning `main` to a clean state:

```bash
START_AT=3 ./automation/run-resolveflow-loop.sh
```

Change `3` to the stage number:

```text
0 plan
1 foundation
2 retrieval
3 agent safety
4 actions/audit
5 Replay/gate
6 public/validation tooling
7 final audit
8 publication preparation
```

Run only one stage:

```bash
START_AT=4 STOP_AFTER=4 ./automation/run-resolveflow-loop.sh
```

## 6. Complete the real human gate

After stage 6:

```bash
cp docs/HUMAN_SIGNOFF.example.json docs/HUMAN_SIGNOFF.json
```

Then complete the required work truthfully:

- at least 36 genuinely human-authored incident truths;
- gate rules locked before held-out evaluation;
- held-out files locked by checksum;
- at least 3 relevant practitioners across at least 10 cases;
- either a fluent-human-validated language slice or removal of the multilingual quality claim.

Update `docs/HUMAN_SIGNOFF.json` with evidence paths, commit it directly to `main`, and push.

Do not put names, employer-confidential data, credentials, or API keys in that file.

## 7. Run the final audit

```bash
START_AT=7 STOP_AFTER=7 ./automation/run-resolveflow-loop.sh
```

## 8. Prepare publication only after the final audit

```bash
START_AT=8 STOP_AFTER=8 RUN_PUBLISH=1 ./automation/run-resolveflow-loop.sh
```

The publication stage prepares and pushes the deployment configuration. Verify the resulting GitHub Pages or other static deployment yourself before claiming that the site is live.

## Useful controls

Disable the backup tag:

```bash
CREATE_BACKUP_TAG=0 ./automation/run-resolveflow-loop.sh
```

Disable Codex network access:

```bash
NETWORK_ACCESS=false ./automation/run-resolveflow-loop.sh
```

Change the model:

```bash
MODEL=gpt-5.6-terra ./automation/run-resolveflow-loop.sh
```

Allow three Codex repair attempts per stage:

```bash
MAX_ATTEMPTS=3 ./automation/run-resolveflow-loop.sh
```

Checkpoint pushes are enabled by default so long milestones remain visible on `main`. Disable them for a single completion commit per stage with:

```bash
PUSH_STAGE_CHECKPOINTS=0 ./automation/run-resolveflow-loop.sh
```

Store logs somewhere else:

```bash
CODEX_LOG_DIR="$HOME/my-codex-logs" ./automation/run-resolveflow-loop.sh
```

## Important behavior

The loop is finite, sequential, and fail-closed. It does not keep retrying forever. It never evaluates model-written shell commands with `eval`. It does not expose the Cohere key to ordinary build stages. The outer script—not Codex—owns checkpoint and completion commits and pushes.

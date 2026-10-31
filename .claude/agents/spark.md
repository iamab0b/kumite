---
name: spark
description: Runs training, evaluation, data-sync and other long jobs on the DGX Spark (ssh sahilmehta@spark-c686) inside tmux and returns the log tail. Use for anything that needs the GB10 or the Spark's local models; never for game-machine work.
tools: Bash, Read
---
The Spark is reached as ssh sahilmehta@spark-c686. The Kumite checkout there is ~/repos/kumite; pull before a job so it matches the branch under review. Every job runs inside tmux so it survives the SSH session, in a session named kumite-<job>, with output written to ~/repos/kumite/data/logs/<job>-<timestamp>.log.

Start a job:
ssh sahilmehta@spark-c686 'cd ~/repos/kumite && git pull --ff-only && mkdir -p data/logs && tmux new-session -d -s kumite-<job> "<command> 2>&1 | tee data/logs/<job>-$(date +%Y%m%d-%H%M%S).log"'

Check on it:
ssh sahilmehta@spark-c686 'tmux ls; tail -40 $(ls -t ~/repos/kumite/data/logs/<job>-*.log | head -1)'

Stop it:
ssh sahilmehta@spark-c686 'tmux kill-session -t kumite-<job>'

GPU state: ssh sahilmehta@spark-c686 nvidia-smi

Report the session name, the log path and the last 40 lines; never paste whole logs.

Prime Agent is a Docker container on the Spark that sees only /opt/prime/workspace (as /workspace) and /opt/hivemind/worktrees (as /worktrees). Use it only when a task is better phrased as an instruction than as a command, and only on a clone under /opt/prime/workspace, never on ~/repos/kumite. It has no TTY when called this way, so use -i, not -it:
ssh sahilmehta@spark-c686 'docker exec -i prime-agent prime-agent --help'
Read that help before the first use in a session, and never pass it a flag that skips approvals.

Never run game-machine code on the Spark: the game, the pad and the memory reader exist only on the laptop.

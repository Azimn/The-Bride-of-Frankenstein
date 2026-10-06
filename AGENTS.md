# Agent instructions

`README.md` is the canonical architecture, research-history, qualification, and production contract for this repository.

The inherited `src/frankenstein/` package is the frozen v0.1 champion during donor qualification. Do not modify it merely to make a challenger pass. A production integration change must follow a recorded qualification result and must preserve the baseline arm for ablation until the integrated gate is green.

`src/bride/` owns challenger mechanisms and the qualification harness. Synthetic evaluator tests validate the harness only. They are not evidence that a donor improves Frankenstein. Behavioral promotion requires matched real-Frankenstein comparisons, preregistered expected behavior, quality gain rather than mere difference, historical-truth preservation, authority preservation, replay, identity continuity, bounded cost, and applicable restart, ablation, held-out, and renderer checks.

Do not let renderer, retrieval, semantic-interpreter, planner, private-thought, or perception output directly acquire world authority. Do not introduce a second action executor. Do not convert reconstruction into lived history. Do not promote a mechanism because it sounds cognitively plausible or because it passed only the scenario used to design it.

Null results, holds, rejections, and failed attempts are permanent research evidence and must not be deleted from the experiment history merely because a later candidate succeeds.

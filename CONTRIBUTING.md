# Contributing

Run the synthetic demo and tests before proposing a change:

    python reproduce.py demo
    python -m unittest discover -s tests -v

Do not require health-data downloads in ordinary CI. Bug reports should include Python/OS versions, the command, a minimal synthetic example, expected/observed behavior and relevant error text. Never attach private health records or credentials.

Method changes should explain the estimand, time support, missingness budget, participant grouping, exclusions and uncertainty. Include a meaningful boundary test or independent numerical check. Do not describe processed curves as raw, devices as ground truth, repeated seeds as independent people, or candidate gaps as confirmed disconnections without evidence.

Keep original code MIT and preserve data attribution/licensing. Do not add raw archives to the repository. Regenerate changed summaries from traceable results.

Prediction work belongs to the next milestone. Define targets and person/time splits before fitting models; avoid leakage through overlapping meals or duplicated datasets.

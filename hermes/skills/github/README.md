# GitHub development skills

GitHub workflows follow the same mandatory BDD rule as the software-development
skills.

## Behavioral boundary

GitHub skills are evaluated by externally meaningful states and effects:

- whether the live/current issue state was understood;
- whether the requested software behavior was achieved;
- whether review found material problems without modifying reviewed work;
- whether the intended commit/branch/PR state was actually created or observed;
- whether CI, review, merge, cleanup, and release states are reported separately;
- whether unrelated user work is preserved.

The name of the skill that performed a step is not itself a behavioral
requirement. Routing and 'skill_view' evidence are diagnostic unless a platform
contract explicitly makes a particular routing decision observable.

## Migration status

`github-code-review` has an offline agent-level fixture eval in
`evals/github-code-review/`. Its current Outcome is `UNDEFINED`; deterministic
trajectory checks cover fixture mutation and forbidden commands.

The source-text checks of GitHub skill instructions were removed at the user's
request. Their results did not establish agent behavior. No replacement coverage
is claimed.

`github-pr-workflow` remains intentionally unimplemented.

## Review order

1. establish behavioral scenarios and baseline evidence;
2. review/revise software-development ownership;
3. rerun the same scenarios;
4. review/revise GitHub orchestration and review;
5. define behavioral delivery scenarios;
6. only then implement the delivery owner.

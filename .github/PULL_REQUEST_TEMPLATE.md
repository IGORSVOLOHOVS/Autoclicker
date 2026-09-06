<!--
The branch name already says which issue this is. This body says what a
reviewer needs in order to say yes, and nothing else.

`contribution-policy.yml` checks the things that can be checked: the branch
name, every commit subject, the sign-off, and that this pull request closes an
issue. It cannot check whether the change is right, which is what the rest of
this form is for.
-->

## Closes

<!--
Required. "Closes #12" - the workflow fails without it.

It will not close the issue on merge: GitHub only acts on the keyword for the
default branch, and this merges into `dev`. Close the issue by hand and say
which pull request did it. See docs/workflow.md.
-->
Closes #

## What changed

<!-- One paragraph. What the code does now that it did not do before. -->

## Why this way

<!--
The alternative you rejected and the reason. If there was no alternative,
say so - that is also information.
-->

## How it was verified

<!--
What you actually ran, not what CI will run.
For a defect: the test that failed before and passes now.
-->

```
python scripts/check_before_push.py
```

## Acceptance criteria from the issue

<!-- Copy them here and tick them. An unticked box is a request for changes. -->

- [ ]

## Checklist

- [ ] The branch is named `<code>-<issue>/<type>/<slug>`
- [ ] Every commit is `<type>(<scope>): <subject>` and signed off (`git commit -s`)
- [ ] `python scripts/check_before_push.py` passes locally
- [ ] Tests cover the change, including the empty and invalid cases
- [ ] `CHANGELOG.md` has an entry under `[Unreleased]`
- [ ] Documentation updated, or this change is not user-visible
- [ ] No credential, token or personal path anywhere in the diff

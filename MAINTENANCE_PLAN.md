# Maintenance Plan

## Responsible Maintainer

[PLACEHOLDER: To be confirmed by Aryav Thakur]

Primary maintainer: Aryav Thakur (aryav.thakur@gmail.com)

## Expected Maintenance Period

[PLACEHOLDER: Duration to be approved by authors — suggest minimum 2 years from initial public release]

## Issue Triage

Issues will be triaged on the GitHub issue tracker. Categories:
- **Bug**: Incorrect audit behavior
- **Enhancement**: Feature request
- **Documentation**: Documentation improvement
- **Question**: Usage question

## Bug Fixes

Critical bugs affecting audit correctness will be addressed promptly. Non-critical issues will be addressed as maintainer capacity permits.

## Dependency Updates

Dependencies will be updated periodically to address security vulnerabilities. Major version upgrades will be tested against the existing test suite before release.

## Supported Python Versions

- Currently tested: Python 3.10+ (verified on 3.13)
- End-of-life Python versions will be dropped with notice

## Regression Tests

The 350-test suite serves as the regression baseline. Any code change must pass the full test suite. New features require accompanying tests.

## Benchmark Governance

- The frozen 0.2.0 benchmark (147/160) is historical and will not be re-executed
- Future benchmark versions should correct the `invalid_probability_cells` ground truth
- New benchmark versions must be prospectively frozen before evaluation

## Future Real-World Validation

Real-world validation using independently supplied metabolomics tables is planned. Results will be reported separately from the synthetic benchmark.

## Benchmark-Reference Corrections

The documented benchmark-reference defect (13 cases) will be corrected in the next benchmark version. The correction is a ground-truth update, not a product-code change.

## Release Versioning

Semantic versioning: MAJOR.MINOR.PATCH
- PATCH: bug fixes, documentation updates
- MINOR: new features, alias additions
- MAJOR: breaking changes to audit output structure

## Deprecation Policy

Features will be deprecated with at least one minor version of advance notice before removal.

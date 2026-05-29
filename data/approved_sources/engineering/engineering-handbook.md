# Northstar Widgets Engineering Handbook

Northstar Widgets is a fictitious company used for Ctrl-F demos.

## Development Workflow

Engineering work is tracked in the issue tracker. Each pull request should reference an approved issue and include a short summary, test evidence, and deployment notes when applicable.

Pull requests require at least one reviewer. Changes that affect authentication, authorization, payments, data exports, or production infrastructure require two reviewers.

## Branching

Feature branches should use the format `team/short-description`. Release branches should use the format `release/YYYY-MM-DD`.

Direct commits to the main branch are not allowed except for emergency fixes approved by the engineering manager on call.

## Testing Expectations

Backend changes should include unit or integration tests for new behavior. Frontend changes should include build verification and smoke testing for changed user flows.

Security-sensitive changes must include tests for unauthorized access and failure cases.

## Production Access

Production access is granted only after secure development training is complete and manager approval is recorded.

Production database access is read-only by default. Write access requires incident commander approval and a documented rollback plan.

## Incident Response

The engineer who discovers a production incident should open an incident channel, notify the on-call engineer, and record the customer impact summary.

Severity 1 incidents require updates every 30 minutes until mitigation is complete.

## Contacts

Questions about code review, deployment, or production access should go to the Engineering Manager or the on-call engineer.

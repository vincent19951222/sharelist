## Purpose

Define invite token rotation control for admins.

## Requirements

### Requirement: Admin can rotate invite token
The system MUST allow Admin users to rotate the invite token for a room.

#### Scenario: Admin rotates invite
- **WHEN** an Admin triggers invite rotation
- **THEN** a new invite token is generated and shown to the Admin

### Requirement: Old invite tokens are invalid after rotation
After rotation, the previous invite token MUST be rejected.

#### Scenario: Member uses old invite
- **WHEN** a user attempts to join with the old token
- **THEN** access is denied and the UI prompts for a new invite

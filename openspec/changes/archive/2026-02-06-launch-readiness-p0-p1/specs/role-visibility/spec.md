## ADDED Requirements

### Requirement: User role is visible
The UI MUST display whether the user is Admin or Member.

#### Scenario: Admin enters a room
- **WHEN** the Admin connects and receives the snapshot
- **THEN** the UI shows an Admin role badge

#### Scenario: Member enters a room
- **WHEN** a Member connects and receives the snapshot
- **THEN** the UI shows a Member role badge

### Requirement: Restricted actions are labeled
Admin-only actions MUST be visibly labeled or disabled for Members.

#### Scenario: Member attempts admin action
- **WHEN** a Member selects an admin-only action
- **THEN** the UI indicates that the action is restricted to Admins

## ADDED Requirements

### Requirement: Room lifecycle notice is visible
The UI MUST inform users that rooms expire after 24 hours of inactivity.

#### Scenario: User views a room
- **WHEN** a user is in a room view
- **THEN** the UI shows a clear notice that the room expires after 24 hours of inactivity

#### Scenario: User shares an invite
- **WHEN** a user opens sharing options
- **THEN** the UI includes the 24-hour inactivity notice in the sharing context

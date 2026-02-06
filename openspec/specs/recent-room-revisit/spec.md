## Purpose

Define behavior for re-entering recent rooms.

## Requirements

### Requirement: Recent rooms are accessible
The system MUST provide a Recent Rooms entry point for quick re-entry.

#### Scenario: User selects a recent room
- **WHEN** a user clicks a recent room entry
- **THEN** the system attempts to enter the room using the stored invite token

### Requirement: Expired tokens show guidance
If a recent room token is invalid, the UI MUST explain that a new invite is required.

#### Scenario: Recent room token is invalid
- **WHEN** entry fails due to invalid or rotated token
- **THEN** the UI shows a message guiding the user to request a new invite

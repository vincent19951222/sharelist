## ADDED Requirements

### Requirement: Errors map to consistent UI states
The system MUST present room and auth errors with a consistent UI state rather than ad-hoc alerts.

#### Scenario: Room not found or expired
- **WHEN** the server closes the connection with a room-not-found or expired code
- **THEN** the UI shows a room-not-found error state with a clear next step

#### Scenario: Room full
- **WHEN** the server closes the connection with a room-full code
- **THEN** the UI shows a capacity error state

#### Scenario: Invalid token
- **WHEN** the server closes the connection with an invalid-token code
- **THEN** the UI prompts the user to obtain a new invite

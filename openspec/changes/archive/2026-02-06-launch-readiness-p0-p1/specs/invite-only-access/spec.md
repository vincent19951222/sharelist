## ADDED Requirements

### Requirement: Token is required to join a room
The system MUST require a valid invite token to enter a room. The roomId alone SHALL NOT grant access.

#### Scenario: Access with roomId only
- **WHEN** a user visits `/room/{roomId}` without a token
- **THEN** the system displays the RoomGate and prompts for an invite token

#### Scenario: Access with valid token
- **WHEN** a user visits `/room/{roomId}` with a valid invite token
- **THEN** the system grants access and loads the room snapshot

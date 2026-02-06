## ADDED Requirements

### Requirement: Connection status is visible
The UI MUST display a clear connection state: Connected, Reconnecting, or Offline.

#### Scenario: Connection drops
- **WHEN** the WebSocket disconnects unexpectedly
- **THEN** the UI shows Reconnecting or Offline status

#### Scenario: Connection restored
- **WHEN** the WebSocket reconnects successfully
- **THEN** the UI shows Connected status

### Requirement: Offline actions are blocked
While Offline, the system MUST prevent state-changing actions and MUST explain why.

#### Scenario: User attempts to add an item offline
- **WHEN** the connection state is Offline and the user tries to add an item
- **THEN** the action is blocked and a message explains that the user is offline

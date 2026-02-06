## Purpose

Define minimal collaboration hints in the UI.

## Requirements

### Requirement: Completed items show who finished them
The UI MUST display the user name responsible for completing an item.

#### Scenario: Item is completed
- **WHEN** a user marks an item as done
- **THEN** the item displays the completing user's name

### Requirement: Key actions provide lightweight hints
The UI MUST show a lightweight hint for key actions such as add, delete, or clear.

#### Scenario: Item is deleted
- **WHEN** a user deletes an item
- **THEN** the UI shows a brief hint confirming the action

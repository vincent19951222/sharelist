# Spec: Visual Indicators

## Overview
Display priority levels with color-coded badges for quick visual identification.

## UI Design
```
High   → 🔴 Red badge (bg-red-100 text-red-800)
Medium → 🟡 Yellow badge (bg-yellow-100 text-yellow-800)
Low    → 🟢 Green badge (bg-green-100 text-green-800)
```

## Placement
- Badge appears to the left of task text
- Size: Small, compact pill shape
- Accessibility: Include text label + color

## Responsive Behavior
- Mobile: Smaller badge, text may be hidden on very small screens
- Desktop: Full badge with text label

## Example
```
[High]   Buy milk
[Medium] Call mom
[Low]    Organize bookmarks
```

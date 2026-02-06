# ShareList (Room Todo)

A real-time collaborative checklist app featuring **Instant Rooms**, **No Login Required**, and **Minimalist Auth**. Built with Next.js 16 and FastAPI.

## Features

*   **Instant Collaboration**: Create a room, share the link, and sync checklists in real-time.
*   **Task Priorities**: Assign priority levels (High/Medium/Low) to tasks with visual indicators and filtering.
*   **Private Invite Auth**:
    *   **Admin**: Create room -> Get Admin Token -> Full control (Rename, Clear Done, Reset Invite).
    *   **Member**: Join via invite link or code -> Edit items only.
    *   **Note**: `roomId` is not an invite. A valid token is required to enter a room.
*   **Persistent Storage**: Powered by Supabase PostgreSQL (Asyncpg + SQLModel).
*   **System Hardening**:
    *   Idempotency checks (no double-posts).
    *   Connection keep-alive & auto-reconnect.
    *   Auto-cleanup for expired rooms (24h TTL).

## Tech Stack

*   **Frontend**: Next.js 16 (App Router), TypeScript, Tailwind CSS, Shadcn/ui.
*   **Backend**: Python 3.11, FastAPI, WebSockets, SQLModel.
*   **Database**: Supabase PostgreSQL (Session Pooler).

## Getting Started (Local Development)

1.  **Install Dependencies**:
    ```bash
    npm run install:all
    ```

2.  **Setup Environment**:
    *   Create `backend/.env` with your Supabase connection string.
    *   (See `docs/STARTUP_GUIDE.md` for details).

3.  **Run Development Server**:
    ```bash
    npm run dev
    ```
    *   Frontend: http://localhost:3000
    *   Backend: http://localhost:8000

## Deployment (Docker)

Deploy the entire stack with one command.

1.  **Build and Run**:
    ```bash
    docker-compose up --build -d
    ```

2.  **Access**:
    Open http://localhost:3000 in your browser.

> **Note**: If deploying to a remote server, update `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` in `docker-compose.yml` to your server's IP/Domain, and rebuild.

## Documentation

*   [Event Protocol](./docs/EVENT_PROTOCOL.md)
*   [QA Checklist](./docs/QA_CHECKLIST.md)
*   [Development Log](./log.md)

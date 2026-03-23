"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { accessRoom } from "@/lib/api";
import { getLocalUser, saveLocalUser } from "@/lib/store";
import styles from "./entry-page.module.css";

export default function HomePage() {
  const router = useRouter();
  const [roomId, setRoomId] = useState("");
  const [name, setName] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const localUser = getLocalUser();
    if (localUser?.name) {
      setName(localUser.name);
      setRoomId(localUser.roomId);
    }
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const response = await accessRoom(roomId.trim(), name.trim());
      saveLocalUser(response.room.roomId, response.user);
      router.push(`/room/${response.room.roomId}`);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "进入房间失败，请稍后再试。");
      setIsSubmitting(false);
    }
  }

  return (
    <div className={styles.entryViewport}>
      <div className={styles.appContainer}>
        <div className={`${styles.page} ${styles.pageLogin}`}>
          <div className={styles.entryShell}>
            <section className={styles.entryHeroCard}>
              <div className={styles.entryBrandRow}>
                <div className={`${styles.logoBox} ${styles.entryLogoBox}`}>
                  <svg aria-hidden="true" viewBox="0 0 24 24">
                    <path d="M4 22V10l4-4v4h8V6l4 4v12H4zm2-2h12v-8h-2v4h-8v-4H6v8zm4-8h4V8h-4v4z" />
                  </svg>
                </div>
                <div className={styles.entryBrandCopy}>
                  <span className={styles.entryKicker}>ROOM TODO</span>
                  <h1 className={styles.entryTitle}>Join Room</h1>
                </div>
              </div>

              <div className={styles.entryHeroVisual}>
                <img alt="Room Todo preview" src="/todolist.png" />
              </div>
            </section>

            <section className={styles.entryFormCard}>
              <div className={styles.entryFormHead}>
                <span className={`${styles.sectionTitle} ${styles.entryFormTitle}`}>ROOM ACCESS</span>
              </div>

              <form onSubmit={handleSubmit}>
                <div className={styles.inputGroup}>
                  <label htmlFor="room-id">ROOM ID</label>
                  <div className={styles.inputWrapper}>
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <path d="M12.65 10C11.83 7.67 9.61 6 7 6c-3.31 0-6 2.69-6 6s2.69 6 6 6c2.61 0 4.83-1.67 5.65-4H17v4h4v-4h2v-4H12.65zM7 14c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z" />
                    </svg>
                    <input
                      id="room-id"
                      autoComplete="off"
                      placeholder="Enter code..."
                      type="text"
                      value={roomId}
                      onChange={(event) => setRoomId(event.target.value)}
                    />
                  </div>
                </div>

                <div className={styles.inputGroup}>
                  <label htmlFor="user-name">YOUR NAME</label>
                  <div className={styles.inputWrapper}>
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                    </svg>
                    <input
                      id="user-name"
                      autoCapitalize="none"
                      autoComplete="off"
                      placeholder="Adventurer name"
                      type="text"
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                    />
                  </div>
                </div>

                {errorMessage ? <div className={styles.entryError}>{errorMessage}</div> : null}

                <button
                  aria-busy={isSubmitting}
                  className={styles.btnStart}
                  disabled={isSubmitting}
                  type="submit"
                >
                  <svg
                    aria-hidden="true"
                    fill="none"
                    height="20"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    viewBox="0 0 24 24"
                    width="20"
                  >
                    <line x1="12" x2="12" y1="5" y2="19" />
                    <line x1="5" x2="19" y1="12" y2="12" />
                  </svg>
                  START QUEST
                </button>
              </form>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}

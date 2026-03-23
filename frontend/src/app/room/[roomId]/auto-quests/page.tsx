"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { DAY_ORDER, REWARD_OPTIONS, weekdayPillLabel } from "@/lib/quest-ui";
import { getLocalUser } from "@/lib/store";
import { useRoomSocket } from "@/lib/use-room-socket";
import { AutoQuest, LocalUser } from "@/types";
import styles from "./auto-quests-page.module.css";

type EditorMode =
  | { type: "create" }
  | { type: "edit"; autoQuest: AutoQuest };

function formatRepeat(days: string[]): string {
  if (days.length === 0) {
    return "Off";
  }

  if (days.length === 7) {
    return "Everyday";
  }

  return days.join(", ");
}

export default function AutoQuestsPage({ params }: { params: Promise<{ roomId: string }> }) {
  const { roomId } = use(params);
  const router = useRouter();
  const [localUser, setLocalUser] = useState<LocalUser | null>(null);
  const [editorMode, setEditorMode] = useState<EditorMode | null>(null);
  const [title, setTitle] = useState("");
  const [rewardGp, setRewardGp] = useState(10);
  const [repeatDays, setRepeatDays] = useState<string[]>(["Wed"]);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    const storedUser = getLocalUser();
    if (!storedUser || storedUser.roomId !== roomId) {
      router.replace("/");
      return;
    }
    setLocalUser(storedUser);
  }, [roomId, router]);

  const { snapshot, connectionState, fatalError, serverMessage, clearServerMessage, sendEvent } = useRoomSocket(
    roomId,
    localUser
  );

  useEffect(() => {
    if (serverMessage) {
      const timeout = setTimeout(clearServerMessage, 2600);
      return () => clearTimeout(timeout);
    }
  }, [clearServerMessage, serverMessage]);

  function openCreate() {
    setEditorMode({ type: "create" });
    setTitle("");
    setRewardGp(10);
    setRepeatDays(["Wed"]);
    setLocalError(null);
  }

  function openEdit(autoQuest: AutoQuest) {
    setEditorMode({ type: "edit", autoQuest });
    setTitle(autoQuest.title);
    setRewardGp(autoQuest.rewardGp);
    setRepeatDays(autoQuest.repeatDays);
    setLocalError(null);
  }

  function closeEditor() {
    setEditorMode(null);
    setLocalError(null);
  }

  function toggleDay(day: string) {
    setRepeatDays((current) =>
      current.includes(day) ? current.filter((value) => value !== day) : [...current, day]
    );
  }

  function saveQuest() {
    if (!title.trim()) {
      setLocalError("Auto Quest name is required.");
      return;
    }

    if (repeatDays.length === 0) {
      setLocalError("Pick at least one repeat day.");
      return;
    }

    const payload = {
      title: title.trim(),
      rewardGp,
      repeatDays,
    };

    const ok =
      editorMode?.type === "edit"
        ? sendEvent("auto_quest_update", {
            autoQuestId: editorMode.autoQuest.id,
            ...payload,
          })
        : sendEvent("auto_quest_create", payload);

    if (!ok) {
      setLocalError("Connection is offline. Try again in a moment.");
      return;
    }

    closeEditor();
  }

  if (!localUser) {
    return (
      <div className={styles.autoViewport}>
        <div className={styles.stateScreen}>
          <div className={styles.spinnerRow}>
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Loading auto quest access…</span>
          </div>
        </div>
      </div>
    );
  }

  if (fatalError) {
    return (
      <div className={styles.autoViewport}>
        <div className={styles.stateScreen}>
          <div className={styles.stateCard}>
            <p className={styles.stateKicker}>Access Lost</p>
            <h1 className={styles.stateTitle}>Room unavailable</h1>
            <p className={styles.stateText}>{fatalError}</p>
            <Link className={styles.stateAction} href="/">
              Back To Entry
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!snapshot) {
    return (
      <div className={styles.autoViewport}>
        <div className={styles.stateScreen}>
          {serverMessage ? (
            <div className={styles.stateCard}>
              <p className={styles.stateKicker}>Realtime Sync</p>
              <h1 className={styles.stateTitle}>Auto quests unavailable</h1>
              <p className={styles.stateText}>{serverMessage}</p>
              <p className={styles.stateText}>Connection state: {connectionState}</p>
              <Link className={styles.stateAction} href="/">
                Back To Entry
              </Link>
            </div>
          ) : (
            <div className={styles.spinnerRow}>
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Syncing auto quests…</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={styles.autoViewport}>
      <div className={styles.autoContainer}>
        <div className={styles.pageAutoQuest}>
          <div className={styles.autoInner}>
            <div className={styles.headerSimple}>
              <Link aria-label="Go back" className={styles.btnBack} href={`/room/${roomId}`}>
                <svg fill="none" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
                  <line x1="19" x2="5" y1="12" y2="12" />
                  <polyline points="12 19 5 12 12 5" />
                </svg>
              </Link>
              <h2>Auto Quests</h2>
            </div>

            {serverMessage || localError ? (
              <div className={styles.feedbackCard}>{localError || serverMessage}</div>
            ) : null}

            <div className={styles.autoQuestStage}>
              <div className={styles.aqStack}>
                {snapshot.autoQuests.length === 0 ? (
                  <div className={styles.emptyCard}>
                    <div className={styles.emptyTitle}>No auto quests yet</div>
                    <div className={styles.emptyText}>
                      每周固定任务建在这里。进入房间时，系统会按上海时区自动补今天的任务实例。
                    </div>
                  </div>
                ) : null}

                {snapshot.autoQuests.map((autoQuest) => (
                  <article
                    className={`${styles.aqCardLarge} ${styles.aqEditableCard}`}
                    key={autoQuest.id}
                    onClick={() => openEdit(autoQuest)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        openEdit(autoQuest);
                      }
                    }}
                    role="button"
                    tabIndex={0}
                  >
                    <div className={styles.aqCardCopy}>
                      <h3 className={styles.aqCardTitle}>{autoQuest.title || "Untitled Quest"}</h3>

                      <div className={styles.aqMetaBlock}>
                        <div className={styles.taskGp}>
                          <div className={styles.coinIcon} />
                          +{autoQuest.rewardGp} GP
                        </div>

                        <div className={`${styles.aqMetaLine} ${styles.aqRepeatLine}`}>
                          <svg fill="none" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
                            <path d="M21 12a9 9 0 0 1-15.5 6.36" />
                            <polyline points="3 16 5.5 18.5 8 16" />
                            <path d="M3 12a9 9 0 0 1 15.5-6.36" />
                            <polyline points="21 8 18.5 5.5 16 8" />
                          </svg>
                          {formatRepeat(autoQuest.repeatDays)}
                        </div>
                      </div>
                    </div>

                    <button
                      aria-label={autoQuest.isEnabled ? "Disable auto quest" : "Enable auto quest"}
                      className={styles.aqToggleButton}
                      onClick={(event) => {
                        event.stopPropagation();
                        const ok = sendEvent("auto_quest_toggle", {
                          autoQuestId: autoQuest.id,
                          isEnabled: !autoQuest.isEnabled,
                        });
                        if (!ok) {
                          setLocalError("Connection is offline. Try again in a moment.");
                        }
                      }}
                      type="button"
                    >
                      <div className={`${styles.aqToggle} ${autoQuest.isEnabled ? styles.aqToggleOn : ""}`} />
                    </button>
                  </article>
                ))}
              </div>
            </div>

            <div className={styles.bottomFixedBtn}>
              <button className={styles.btnCapsule} onClick={openCreate} type="button">
                <svg fill="none" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
                  <line x1="12" x2="12" y1="5" y2="19" />
                  <line x1="5" x2="19" y1="12" y2="12" />
                </svg>
                New Auto quest
              </button>
            </div>
          </div>
        </div>
      </div>

      {editorMode ? (
        <>
          <button className={styles.aqEditorOverlay} onClick={closeEditor} type="button" />
          <div className={styles.aqEditorPanel}>
            <div className={styles.aqEditorHeader}>
              <div>
                <span className={styles.aqEditorKicker}>Auto Quest</span>
                <h3>{editorMode.type === "edit" ? "Edit Quest" : "New Auto Quest"}</h3>
              </div>
              <button
                aria-label="Close editor"
                className={styles.aqEditorClose}
                onClick={closeEditor}
                type="button"
              >
                <svg fill="none" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
                  <line x1="18" x2="6" y1="6" y2="18" />
                  <line x1="6" x2="18" y1="6" y2="18" />
                </svg>
              </button>
            </div>

            <div className={styles.aqFormField}>
              <label htmlFor="aq-input-name">Quest Name</label>
              <input
                className={styles.aqInput}
                id="aq-input-name"
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Water plants"
                type="text"
                value={title}
              />
            </div>

            <div className={styles.aqFormField}>
              <label htmlFor="aq-input-gp">Reward</label>
              <select
                className={`${styles.aqInput} ${styles.aqSelect}`}
                id="aq-input-gp"
                onChange={(event) => setRewardGp(Number(event.target.value))}
                value={rewardGp}
              >
                {REWARD_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option} GP
                  </option>
                ))}
              </select>
            </div>

            <div className={styles.aqFormField}>
              <label>Repeat On</label>
              <div className={styles.aqDayGrid}>
                {DAY_ORDER.map((day) => {
                  const selected = repeatDays.includes(day);
                  return (
                    <button
                      className={`${styles.aqDayBtn} ${selected ? styles.aqDayBtnSelected : ""}`}
                      key={day}
                      onClick={() => toggleDay(day)}
                      type="button"
                    >
                      {weekdayPillLabel(day)}
                    </button>
                  );
                })}
              </div>
            </div>

            <button className={styles.aqSaveBtn} onClick={saveQuest} type="button">
              Save Changes
            </button>
          </div>
        </>
      ) : null}
    </div>
  );
}

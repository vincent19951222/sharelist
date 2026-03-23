"use client";

import { use, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { REWARD_OPTIONS } from "@/lib/quest-ui";
import { clearLocalUser, getLocalUser } from "@/lib/store";
import { useRoomSocket } from "@/lib/use-room-socket";
import { LocalUser } from "@/types";
import styles from "./room-page.module.css";

export default function RoomPage({ params }: { params: Promise<{ roomId: string }> }) {
  const { roomId } = use(params);
  const router = useRouter();
  const [localUser, setLocalUser] = useState<LocalUser | null>(null);
  const [draftTitle, setDraftTitle] = useState("");
  const [draftReward, setDraftReward] = useState(10);
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [editingReward, setEditingReward] = useState(10);
  const [localError, setLocalError] = useState<string | null>(null);
  const [rewardMenuOpen, setRewardMenuOpen] = useState(false);
  const rewardPickerRef = useRef<HTMLDivElement | null>(null);
  const composerInputRef = useRef<HTMLInputElement | null>(null);
  const composerBubbleRef = useRef<HTMLDivElement | null>(null);

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

  const activeMembers = snapshot?.members ?? [];
  const displayItems = snapshot?.items ?? [];

  useEffect(() => {
    if (!editingItemId) {
      return;
    }

    const editingItem = displayItems.find((item) => item.id === editingItemId);
    if (!editingItem) {
      cancelEditing();
    }
  }, [displayItems, editingItemId]);

  useEffect(() => {
    if (!editingItemId) {
      return;
    }

    const frame = window.requestAnimationFrame(() => {
      composerBubbleRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });

      if (composerInputRef.current) {
        composerInputRef.current.focus();
        const end = composerInputRef.current.value.length;
        composerInputRef.current.setSelectionRange(end, end);
      }
    });

    return () => window.cancelAnimationFrame(frame);
  }, [editingItemId]);

  useEffect(() => {
    if (!rewardMenuOpen) {
      return;
    }

    function handlePointerDown(event: MouseEvent) {
      if (!rewardPickerRef.current?.contains(event.target as Node)) {
        setRewardMenuOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setRewardMenuOpen(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [rewardMenuOpen]);

  function handleAddItem() {
    setLocalError(null);
    if (!draftTitle.trim()) {
      setLocalError("Quest name is required.");
      return;
    }
    const ok = sendEvent("item_add", {
      title: draftTitle.trim(),
      rewardGp: draftReward,
    });
    if (!ok) {
      setLocalError("Connection is offline. Try again in a moment.");
      return;
    }
    setDraftTitle("");
    setDraftReward(10);
    setRewardMenuOpen(false);
  }

  function startEditing(itemId: string, title: string, rewardGp: number) {
    if (editingItemId === itemId) {
      cancelEditing();
      return;
    }
    setEditingItemId(itemId);
    setEditingTitle(title);
    setEditingReward(rewardGp);
    setLocalError(null);
  }

  function cancelEditing() {
    setEditingItemId(null);
    setEditingTitle("");
    setEditingReward(10);
    setRewardMenuOpen(false);
  }

  function saveEditing() {
    if (!editingItemId) {
      return;
    }
    if (!editingTitle.trim()) {
      setLocalError("Quest name is required.");
      return;
    }
    const ok = sendEvent("item_edit", {
      itemId: editingItemId,
      title: editingTitle.trim(),
      rewardGp: editingReward,
    });
    if (!ok) {
      setLocalError("Connection is offline. Try again in a moment.");
      return;
    }
    cancelEditing();
  }

  function handleComposerSubmit() {
    if (editingItemId) {
      saveEditing();
      return;
    }
    handleAddItem();
  }

  function setComposerTitle(nextTitle: string) {
    if (editingItemId) {
      setEditingTitle(nextTitle);
      return;
    }
    setDraftTitle(nextTitle);
  }

  function setComposerReward(nextReward: number) {
    if (editingItemId) {
      setEditingReward(nextReward);
      return;
    }
    setDraftReward(nextReward);
  }

  function handleLeave() {
    clearLocalUser();
    router.push("/");
  }

  const composerTitle = editingItemId ? editingTitle : draftTitle;
  const composerReward = editingItemId ? editingReward : draftReward;

  if (!localUser) {
    return (
      <div className={styles.roomViewport}>
        <div className={styles.stateScreen}>
          <div className={styles.spinnerRow}>
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Loading room access…</span>
          </div>
        </div>
      </div>
    );
  }

  if (fatalError) {
    return (
      <div className={styles.roomViewport}>
        <div className={styles.stateScreen}>
          <div className={styles.stateCard}>
            <p className={styles.stateKicker}>Access Lost</p>
            <h1 className={styles.stateTitle}>Room unavailable</h1>
            <p className={styles.stateText}>{fatalError}</p>
            <button className={styles.stateAction} onClick={handleLeave} type="button">
              Back To Entry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!snapshot) {
    return (
      <div className={styles.roomViewport}>
        <div className={styles.stateScreen}>
          {serverMessage ? (
            <div className={styles.stateCard}>
              <p className={styles.stateKicker}>Realtime Sync</p>
              <h1 className={styles.stateTitle}>Snapshot unavailable</h1>
              <p className={styles.stateText}>{serverMessage}</p>
              <p className={styles.stateText}>Connection state: {connectionState}</p>
              <button className={styles.stateAction} onClick={handleLeave} type="button">
                Back To Entry
              </button>
            </div>
          ) : (
            <div className={styles.spinnerRow}>
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Syncing room snapshot…</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={styles.roomViewport}>
      <div className={styles.roomContainer}>
        <div className={styles.pageRoom}>
          <div className={styles.roomInner}>
            <header className={styles.header}>
              <div className={styles.hLeft}>
                <Link className={styles.avatarMain} href={`/room/${roomId}/profile`}>
                  <img alt={snapshot.currentUser.displayName} src={snapshot.currentUser.avatarUrl} />
                  <div
                    className={`${styles.statusDot} ${
                      connectionState === "connected" ? "" : styles.statusDotOffline
                    }`}
                  />
                </Link>
                <div className={styles.titleBox}>
                  <span className={styles.tSub}>TITLE</span>
                  <span className={styles.tMain}>{snapshot.room.title}</span>
                </div>
              </div>

              <div className={styles.hRight}>
                <div className={styles.roomId}>
                  ID <span>#{snapshot.room.roomId}</span>
                </div>
                <div className={styles.memberGroup}>
                  {activeMembers.map((member) => (
                    <img alt={member.displayName} key={member.userId} src={member.avatarUrl} />
                  ))}
                </div>
              </div>
            </header>

            <div className={styles.listBody}>
              <div className={styles.sectionBar}>
                <div className={styles.sectionTitle}>
                  <svg
                    fill="none"
                    height="16"
                    stroke="currentColor"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    width="16"
                  >
                    <rect height="18" rx="2" ry="2" width="18" x="3" y="4" />
                    <line x1="16" x2="16" y1="2" y2="6" />
                    <line x1="8" x2="8" y1="2" y2="6" />
                    <line x1="3" x2="21" y1="10" y2="10" />
                  </svg>
                  TODAY&apos;S QUEST
                </div>
                <Link className={styles.sectionLinkChip} href={`/room/${roomId}/auto-quests`}>
                  <span className={styles.sectionLinkDot} />
                  Auto Quests
                </Link>
              </div>

              {serverMessage || localError ? (
                <div className={styles.feedbackCard}>{localError || serverMessage}</div>
              ) : null}

              <div className={styles.taskList}>
                {displayItems.length === 0 ? (
                  <div className={styles.emptyCard}>
                    <div className={styles.emptyTitle}>Quest board is empty</div>
                    <div className={styles.emptyText}>
                      新增一条任务，或者先去 Auto Quests 页配置固定重复任务。
                    </div>
                  </div>
                ) : null}

                {displayItems.map((item) => {
                  const isEditing = editingItemId === item.id;
                  const metaText = item.done
                    ? item.completedBy
                      ? `Completed by @${item.completedBy}`
                      : null
                    : item.createdBy
                      ? `Added by @${item.createdBy}`
                      : null;

                  return (
                    <article
                      className={`${styles.taskCard} ${item.done ? styles.completed : ""} ${
                        isEditing ? styles.activeEditing : ""
                      }`}
                      key={item.id}
                      onClick={() => startEditing(item.id, item.title, item.rewardGp)}
                    >
                      <label
                        className={styles.checkboxContainer}
                        onClick={(event) => event.stopPropagation()}
                      >
                        <input
                          checked={item.done}
                          onChange={() => {
                            setLocalError(null);
                            const ok = sendEvent("item_toggle", { itemId: item.id, done: !item.done });
                            if (!ok) {
                              setLocalError("Connection is offline. Try again in a moment.");
                            }
                          }}
                          type="checkbox"
                        />
                        <span className={styles.checkmark} />
                      </label>

                      <button
                        className={styles.taskContentButton}
                        onClick={(event) => {
                          event.stopPropagation();
                          startEditing(item.id, item.title, item.rewardGp);
                        }}
                        type="button"
                      >
                        <div className={styles.taskContent}>
                          <div className={styles.taskName}>{item.title}</div>
                          {isEditing ? (
                            <div className={`${styles.taskMeta} ${styles.highlight}`}>
                              <img
                                alt={snapshot.currentUser.displayName}
                                src={snapshot.currentUser.avatarUrl}
                              />
                              {snapshot.currentUser.displayName} is editing...
                            </div>
                          ) : metaText ? (
                            <div className={styles.taskMeta}>{metaText}</div>
                          ) : null}
                          {item.rewardGp > 0 ? (
                            <div className={styles.taskGp}>
                              <div className={styles.coinIcon} /> +{item.rewardGp} GP
                            </div>
                          ) : null}
                        </div>
                      </button>

                      {isEditing ? (
                        <button
                          className={styles.iconTrash}
                          onClick={(event) => {
                            event.stopPropagation();
                            setLocalError(null);
                            const ok = sendEvent("item_delete", { itemId: item.id });
                            if (!ok) {
                              setLocalError("Connection is offline. Try again in a moment.");
                              return;
                            }
                            cancelEditing();
                          }}
                          type="button"
                        >
                          <svg viewBox="0 0 24 24">
                            <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" />
                          </svg>
                        </button>
                      ) : null}
                    </article>
                  );
                })}
              </div>
            </div>

            <div className={styles.bottomBubbleContainer}>
              <div className={styles.chatBubble} ref={composerBubbleRef}>
                <input
                  className={styles.bubbleInput}
                  ref={composerInputRef}
                  onChange={(event) => setComposerTitle(event.target.value)}
                  onFocus={() => setLocalError(null)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.preventDefault();
                      handleComposerSubmit();
                    }
                    if (event.key === "Escape" && editingItemId) {
                      cancelEditing();
                    }
                  }}
                  placeholder="Laundry Day"
                  type="text"
                  value={composerTitle}
                />
                <div className={styles.bubbleDivider} />
                <div className={styles.bubbleActions}>
                  <div className={styles.bubblePills}>
                    <div className={styles.rewardPicker} ref={rewardPickerRef}>
                      <button
                        aria-controls="reward-menu"
                        aria-expanded={rewardMenuOpen}
                        className={`${styles.bPill} ${styles.pillYellow} ${styles.rewardTrigger}`}
                        id="reward-trigger"
                        onClick={() => setRewardMenuOpen((current) => !current)}
                        type="button"
                      >
                        <div className={styles.coinIcon} />
                        Reward <b>{composerReward} GP</b>
                        <svg
                          className={styles.rewardCaret}
                          fill="none"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          viewBox="0 0 24 24"
                        >
                          <polyline points="6 9 12 15 18 9" />
                        </svg>
                      </button>
                      {rewardMenuOpen ? (
                        <div className={styles.rewardMenu} id="reward-menu">
                          {REWARD_OPTIONS.map((option) => (
                            <button
                              className={styles.rewardOption}
                              key={option}
                              onClick={() => {
                                setComposerReward(option);
                                setRewardMenuOpen(false);
                              }}
                              type="button"
                            >
                              {option} GP
                            </button>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  </div>
                  <button
                    aria-label={editingItemId ? "Save quest changes" : "Add quest"}
                    className={styles.btnAdd}
                    onClick={handleComposerSubmit}
                    type="button"
                  >
                    <svg fill="none" viewBox="0 0 24 24">
                      <line x1="12" x2="12" y1="5" y2="19" />
                      <line x1="5" x2="19" y1="12" y2="12" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

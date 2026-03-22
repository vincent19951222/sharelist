"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { getProfile } from "@/lib/api";
import { formatHistoryTime } from "@/lib/quest-ui";
import { getLocalUser } from "@/lib/store";
import { LocalUser, ProfileSummary } from "@/types";
import styles from "./profile-page.module.css";

export default function ProfilePage({ params }: { params: Promise<{ roomId: string }> }) {
  const { roomId } = use(params);
  const router = useRouter();
  const [localUser, setLocalUser] = useState<LocalUser | null>(null);
  const [profile, setProfile] = useState<ProfileSummary | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const storedUser = getLocalUser();
    if (!storedUser || storedUser.roomId !== roomId) {
      router.replace("/");
      return;
    }
    setLocalUser(storedUser);
  }, [roomId, router]);

  useEffect(() => {
    if (!localUser) {
      return;
    }

    let cancelled = false;
    getProfile(roomId, localUser.userId)
      .then((response) => {
        if (!cancelled) {
          setProfile(response);
          setErrorMessage(null);
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setErrorMessage(error instanceof Error ? error.message : "Failed to load profile.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [localUser, roomId]);

  if (!localUser || (!profile && !errorMessage)) {
    return (
      <div className={styles.profileViewport}>
        <div className={styles.stateScreen}>
          <div className={styles.spinnerRow}>
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Loading profile…</span>
          </div>
        </div>
      </div>
    );
  }

  if (errorMessage || !profile) {
    return (
      <div className={styles.profileViewport}>
        <div className={styles.stateScreen}>
          <div className={styles.stateCard}>
            <p className={styles.stateKicker}>Profile Error</p>
            <h1 className={styles.stateTitle}>Can&apos;t load profile</h1>
            <p className={styles.stateText}>{errorMessage}</p>
            <Link className={styles.stateAction} href={`/room/${roomId}`}>
              Back To Room
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.profileViewport}>
      <div className={styles.profileContainer}>
        <div className={styles.pageProfile}>
          <div className={styles.profileInner}>
            <div className={styles.headerSimple}>
              <Link aria-label="Go back" className={styles.btnBack} href={`/room/${roomId}`}>
                <svg fill="none" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
                  <line x1="19" x2="5" y1="12" y2="12" />
                  <polyline points="12 19 5 12 12 5" />
                </svg>
              </Link>
              <h2>Profile</h2>
            </div>

            <div className={styles.profileBody}>
              <section className={styles.profileHero}>
                <div className={styles.profileHeroTop}>
                  <div className={styles.profileUser}>
                    <div className={styles.profileAvatar}>
                      <img alt="Profile avatar" src={profile.avatarUrl} />
                    </div>
                    <div className={styles.profileUserCopy}>
                      <span className={styles.profileKicker}>PLAYER PROFILE</span>
                      <h3>{profile.displayName}</h3>
                      <div className={styles.profileUserName}>@{profile.name}</div>
                    </div>
                  </div>
                  <span className={styles.profileRank}>Rank {profile.rank}</span>
                </div>

                <div className={styles.profileTotalPanel}>
                  <span className={styles.profileTotalLabel}>Total Coins</span>
                  <div className={styles.profileTotalValue}>
                    <span className={styles.profileCoinBadge}>
                      <span className={styles.coinIcon} />
                    </span>
                    <strong>{profile.totalGp.toLocaleString("en-US")}</strong>
                  </div>
                </div>

                <div className={styles.profileStatsRow}>
                  <div className={styles.profileStatCard}>
                    <span className={styles.profileStatLabel}>This Week</span>
                    <strong>{profile.thisWeekGp}</strong>
                    <span className={styles.profileStatNote}>+{profile.thisWeekCount} quests</span>
                  </div>
                  <div className={styles.profileStatCard}>
                    <span className={styles.profileStatLabel}>This Month</span>
                    <strong>{profile.thisMonthGp}</strong>
                    <span className={styles.profileStatNote}>+{profile.thisMonthCount} quests</span>
                  </div>
                </div>
              </section>

              <section className={styles.profileHistory}>
                <div className={`${styles.sectionBar} ${styles.profileSectionBar}`}>
                  <div className={styles.sectionTitle}>
                    <svg
                      fill="none"
                      height="16"
                      stroke="currentColor"
                      strokeWidth="2"
                      viewBox="0 0 24 24"
                      width="16"
                    >
                      <circle cx="12" cy="12" r="9" />
                      <polyline points="12 7 12 12 15 15" />
                    </svg>
                    HISTORY LOG
                  </div>
                </div>

                <div className={styles.historyList}>
                  {profile.history.length === 0 ? (
                    <div className={styles.emptyCard}>
                      <div className={styles.emptyTitle}>No GP yet</div>
                      <div className={styles.emptyText}>
                        完成任务后，这里会记录每一笔有效积分流水。
                      </div>
                    </div>
                  ) : null}

                  {profile.history.map((entry, index) => (
                    <article className={styles.historyItem} key={entry.id}>
                      {index < profile.history.length - 1 ? (
                        <div className={styles.historyLine} />
                      ) : null}
                      <div className={styles.historyDot} />
                      <div className={styles.historyContent}>
                        <div className={styles.historyTop}>
                          <div>
                            <h4>{entry.todoTitle}</h4>
                            <p>{formatHistoryTime(entry.awardedAt)}</p>
                          </div>
                          <span className={styles.historyGp}>+{entry.gpDelta} GP</span>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

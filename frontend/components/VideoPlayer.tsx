"use client";

/** Simple HTML5 video player with caption-download links. */

import { media } from "@/lib/api";
import { cx } from "@/lib/utils";

export function VideoPlayer({
  src,
  poster,
  className,
}: {
  src: string | null;
  poster?: string | null;
  className?: string;
}) {
  const url = media(src);
  const posterUrl = media(poster);
  if (!url) {
    return (
      <div
        className={cx(
          "flex aspect-video items-center justify-center rounded-2xl bg-slate-200 text-sm text-slate-500 dark:bg-slate-800 dark:text-slate-400",
          className
        )}
      >
        No video yet — generate one to preview
      </div>
    );
  }
  return (
    <video
      key={url}
      src={url}
      poster={posterUrl ?? undefined}
      controls
      playsInline
      className={cx(
        "w-full rounded-2xl bg-black shadow-lg ring-1 ring-slate-900/10",
        className
      )}
    />
  );
}

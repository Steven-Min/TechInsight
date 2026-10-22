"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  /** 現在のページ番号（クライアント側カウンタ、1始まり） */
  page: number;
  hasNext: boolean;
  onPrev: () => void;
  onNext: () => void;
}

export function Pagination({ page, hasNext, onPrev, onNext }: PaginationProps) {
  if (page <= 1 && !hasNext) return null;

  return (
    <nav className="flex items-center justify-center gap-2" aria-label="ページネーション">
      <button
        onClick={onPrev}
        disabled={page <= 1}
        className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 transition hover:border-indigo-300 disabled:opacity-40"
      >
        <ChevronLeft size={15} />
        前へ
      </button>
      <span className="px-3 text-sm text-slate-500">{page} ページ目</span>
      <button
        onClick={onNext}
        disabled={!hasNext}
        className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 transition hover:border-indigo-300 disabled:opacity-40"
      >
        次へ
        <ChevronRight size={15} />
      </button>
    </nav>
  );
}

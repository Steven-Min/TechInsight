"use client";

import { CalendarDays, Pencil, Trash2, User } from "lucide-react";
import type { ArticleListItem } from "@/lib/types";

interface ArticleCardProps {
  article: ArticleListItem;
  score?: number;
  onOpen: (id: number) => void;
  onEdit: (id: number) => void;
  onDelete: (id: number) => void;
}

function formatDate(iso: string | null): string {
  if (!iso) return "日付なし";
  return new Date(iso).toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function ArticleCard({ article, score, onOpen, onEdit, onDelete }: ArticleCardProps) {
  return (
    <article
      className="group flex cursor-pointer flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-300 hover:shadow-md"
      onClick={() => onOpen(article.id)}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="flex flex-wrap items-center gap-1.5">
          {article.category && (
            <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700">
              {article.category}
            </span>
          )}
          {score !== undefined && (
            <span
              className="rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700"
              title="検索クエリとの関連度"
            >
              関連度 {(score * 100).toFixed(0)}%
            </span>
          )}
        </div>
        <div
          className="flex shrink-0 gap-1 opacity-0 transition group-hover:opacity-100"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => onEdit(article.id)}
            className="rounded-md p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-indigo-600"
            aria-label={`「${article.title}」を編集`}
          >
            <Pencil size={15} />
          </button>
          <button
            onClick={() => onDelete(article.id)}
            className="rounded-md p-1.5 text-slate-400 transition hover:bg-rose-50 hover:text-rose-600"
            aria-label={`「${article.title}」を削除`}
          >
            <Trash2 size={15} />
          </button>
        </div>
      </div>

      <h3 className="mb-2 line-clamp-2 text-base font-semibold leading-snug text-slate-900 group-hover:text-indigo-700">
        {article.title}
      </h3>
      <p className="mb-3 line-clamp-3 flex-1 text-sm leading-relaxed text-slate-500">
        {article.excerpt}
      </p>

      {article.tags.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-1">
          {article.tags.slice(0, 4).map((tag) => (
            <span
              key={tag}
              className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-600"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center gap-3 text-xs text-slate-400">
        <span className="flex items-center gap-1">
          <CalendarDays size={13} />
          {formatDate(article.published_at)}
        </span>
        {article.author && (
          <span className="flex items-center gap-1">
            <User size={13} />
            {article.author}
          </span>
        )}
      </div>
    </article>
  );
}

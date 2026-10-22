"use client";

import { useQuery } from "@tanstack/react-query";
import { CalendarDays, Pencil, Trash2, User } from "lucide-react";
import { api } from "@/lib/api";
import { Modal } from "./modal";

interface ArticleDetailModalProps {
  articleId: number;
  onClose: () => void;
  onEdit: (id: number) => void;
  onDelete: (id: number) => void;
}

function formatDateTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("ja-JP", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function ArticleDetailModal({
  articleId,
  onClose,
  onEdit,
  onDelete,
}: ArticleDetailModalProps) {
  const { data: article, isLoading, isError } = useQuery({
    queryKey: ["article", articleId],
    queryFn: () => api.getArticle(articleId),
  });

  return (
    <Modal title="記事詳細" onClose={onClose} maxWidth="max-w-3xl">
      {isLoading && (
        <div className="space-y-3 py-4">
          <div className="h-7 w-3/4 animate-pulse rounded bg-slate-200" />
          <div className="h-4 w-1/3 animate-pulse rounded bg-slate-100" />
          <div className="h-40 animate-pulse rounded bg-slate-100" />
        </div>
      )}
      {isError && (
        <p className="py-8 text-center text-sm text-rose-600">
          記事の取得に失敗しました。時間をおいて再度お試しください。
        </p>
      )}
      {article && (
        <div>
          <div className="mb-3 flex flex-wrap items-center gap-2">
            {article.category && (
              <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700">
                {article.category}
              </span>
            )}
            {article.tags.map((tag) => (
              <span
                key={tag}
                className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-600"
              >
                #{tag}
              </span>
            ))}
          </div>

          <h1 className="mb-3 text-xl font-bold leading-snug text-slate-900">
            {article.title}
          </h1>

          <div className="mb-5 flex flex-wrap items-center gap-4 border-b border-slate-100 pb-4 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <CalendarDays size={14} />
              公開: {formatDateTime(article.published_at)}
            </span>
            {article.author && (
              <span className="flex items-center gap-1">
                <User size={14} />
                {article.author}
              </span>
            )}
            <span>最終更新: {formatDateTime(article.updated_at)}</span>
            <div className="ml-auto flex gap-2">
              <button
                onClick={() => onEdit(article.id)}
                className="flex items-center gap-1 rounded-md border border-slate-200 px-2.5 py-1.5 font-medium text-slate-600 transition hover:border-indigo-300 hover:text-indigo-600"
              >
                <Pencil size={13} />
                編集
              </button>
              <button
                onClick={() => onDelete(article.id)}
                className="flex items-center gap-1 rounded-md border border-slate-200 px-2.5 py-1.5 font-medium text-slate-600 transition hover:border-rose-300 hover:text-rose-600"
              >
                <Trash2 size={13} />
                削除
              </button>
            </div>
          </div>

          <div className="article-content text-[15px]">{article.content}</div>
        </div>
      )}
    </Modal>
  );
}

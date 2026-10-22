"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { ArticleInput } from "@/lib/types";
import { Modal } from "./modal";
import { useToast } from "./toast";

interface ArticleFormModalProps {
  articleId: number | null; // null = 新規作成
  onClose: () => void;
}

interface FormState {
  title: string;
  content: string;
  category: string;
  tags: string;
  author: string;
  published_at: string;
}

const EMPTY_FORM: FormState = {
  title: "",
  content: "",
  category: "",
  tags: "",
  author: "",
  published_at: "",
};

// ISO 文字列 → ローカルタイムゾーンでの YYYY-MM-DD（UTC 日付をそのまま切り出すと1日ずれる）
function toLocalDateString(iso: string): string {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function toInput(form: FormState): ArticleInput {
  return {
    title: form.title.trim(),
    content: form.content.trim(),
    category: form.category.trim() || null,
    tags: form.tags
      .split(/[,、]/)
      .map((t) => t.trim())
      .filter(Boolean)
      .slice(0, 20),
    author: form.author.trim() || null,
    // date 入力はローカルタイムゾーンの 0時として解釈する
    published_at: form.published_at
      ? new Date(`${form.published_at}T00:00:00`).toISOString()
      : null,
  };
}

export function ArticleFormModal({ articleId, onClose }: ArticleFormModalProps) {
  const isEdit = articleId !== null;
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [validationError, setValidationError] = useState<string | null>(null);

  // 編集時は既存データをフォームへ反映
  const { data: existing, isLoading: isLoadingExisting } = useQuery({
    queryKey: ["article", articleId],
    queryFn: () => api.getArticle(articleId!),
    enabled: isEdit,
  });

  useEffect(() => {
    if (existing) {
      setForm({
        title: existing.title,
        content: existing.content,
        category: existing.category ?? "",
        tags: existing.tags.join(", "),
        author: existing.author ?? "",
        published_at: existing.published_at
          ? toLocalDateString(existing.published_at)
          : "",
      });
    }
  }, [existing]);

  const mutation = useMutation({
    mutationFn: (input: ArticleInput) =>
      isEdit ? api.updateArticle(articleId!, input) : api.createArticle(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["articles"] });
      queryClient.invalidateQueries({ queryKey: ["search"] });
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      if (isEdit) {
        queryClient.invalidateQueries({ queryKey: ["article", articleId] });
      }
      showToast("success", isEdit ? "記事を更新しました" : "記事を作成しました");
      onClose();
    },
    onError: (error) => {
      const message =
        error instanceof ApiError ? error.message : "保存に失敗しました";
      showToast("error", message);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim() || !form.content.trim()) {
      setValidationError("タイトルと本文は必須です");
      return;
    }
    setValidationError(null);
    mutation.mutate(toInput(form));
  };

  const set = (field: keyof FormState) => (value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const inputClass =
    "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100";

  return (
    <Modal title={isEdit ? "記事を編集" : "記事を投稿"} onClose={onClose}>
      {isEdit && isLoadingExisting ? (
        <div className="space-y-3 py-4">
          <div className="h-10 animate-pulse rounded bg-slate-100" />
          <div className="h-40 animate-pulse rounded bg-slate-100" />
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              タイトル <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => set("title")(e.target.value)}
              maxLength={512}
              className={inputClass}
              placeholder="記事のタイトル"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              本文 <span className="text-rose-500">*</span>
            </label>
            <textarea
              value={form.content}
              onChange={(e) => set("content")(e.target.value)}
              rows={10}
              className={inputClass}
              placeholder="記事の本文（Markdown 可）"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                カテゴリ
              </label>
              <input
                type="text"
                value={form.category}
                onChange={(e) => set("category")(e.target.value)}
                maxLength={128}
                className={inputClass}
                placeholder="例: データベース"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                著者
              </label>
              <input
                type="text"
                value={form.author}
                onChange={(e) => set("author")(e.target.value)}
                maxLength={128}
                className={inputClass}
                placeholder="例: 田中太郎"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                タグ（カンマ区切り）
              </label>
              <input
                type="text"
                value={form.tags}
                onChange={(e) => set("tags")(e.target.value)}
                className={inputClass}
                placeholder="例: postgresql, index"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                公開日
              </label>
              <input
                type="date"
                value={form.published_at}
                onChange={(e) => set("published_at")(e.target.value)}
                className={inputClass}
              />
            </div>
          </div>

          {validationError && (
            <p className="text-sm text-rose-600">{validationError}</p>
          )}

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:opacity-60"
            >
              {mutation.isPending
                ? "保存中…"
                : isEdit
                  ? "更新する"
                  : "投稿する"}
            </button>
          </div>
        </form>
      )}
    </Modal>
  );
}

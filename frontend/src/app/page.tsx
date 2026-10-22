"use client";

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { BookOpen, Plus, SearchX } from "lucide-react";
import { useEffect, useState } from "react";
import { ArticleCard } from "@/components/article-card";
import { ArticleDetailModal } from "@/components/article-detail-modal";
import { ArticleFormModal } from "@/components/article-form-modal";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { Pagination } from "@/components/pagination";
import { SearchBar } from "@/components/search-bar";
import { useToast } from "@/components/toast";
import { api, ApiError } from "@/lib/api";
import type { PaginatedArticles, SearchMode } from "@/lib/types";

const PAGE_SIZE = 12;

function formatTotal(data: PaginatedArticles | undefined): string {
  if (!data) return "全 0 件";
  const n = data.total.toLocaleString("ja-JP");
  switch (data.total_relation) {
    case "gte":
      return `${n}+ 件`;
    case "approx":
      return `約 ${n} 件`;
    default:
      return `全 ${n} 件`;
  }
}

export default function HomePage() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  // --- 検索状態 ---
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<SearchMode>("keyword");
  const [category, setCategory] = useState("");
  // keyset ページネーション: 現在位置に至るカーソルの履歴（空 = 先頭ページ）。
  // 「前へ」は履歴を pop するだけなので、逆方向クエリが不要
  const [cursorStack, setCursorStack] = useState<string[]>([]);
  const cursor = cursorStack[cursorStack.length - 1] ?? null;
  const pageNumber = cursorStack.length + 1;
  // セマンティック / ハイブリッドは送信時に確定するクエリ
  const [submittedQuery, setSubmittedQuery] = useState("");
  // キーワードモードはデバウンスして自動検索
  const [debouncedInput, setDebouncedInput] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedInput(input.trim()), 350);
    return () => clearTimeout(timer);
  }, [input]);

  useEffect(() => {
    setCursorStack([]);
  }, [debouncedInput, category]);

  const isSemanticMode = mode !== "keyword";
  const semanticActive = isSemanticMode && submittedQuery.length > 0;

  // --- データ取得 ---
  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: api.listCategories,
  });

  const listQuery = useQuery({
    queryKey: [
      "articles",
      cursor,
      isSemanticMode ? "" : debouncedInput,
      category,
    ],
    queryFn: () =>
      api.listArticles({
        cursor,
        pageSize: PAGE_SIZE,
        q: isSemanticMode ? undefined : debouncedInput || undefined,
        category: category || undefined,
      }),
    placeholderData: keepPreviousData,
    enabled: !semanticActive,
  });

  const searchQuery = useQuery({
    queryKey: ["search", submittedQuery, mode],
    queryFn: () =>
      api.searchArticles({ q: submittedQuery, mode, limit: 24 }),
    enabled: semanticActive,
  });

  // --- モーダル状態 ---
  const [detailId, setDetailId] = useState<number | null>(null);
  const [formState, setFormState] = useState<
    { open: false } | { open: true; articleId: number | null }
  >({ open: false });
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteArticle(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["articles"] });
      queryClient.invalidateQueries({ queryKey: ["search"] });
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      showToast("success", "記事を削除しました");
      setDeleteId(null);
      setDetailId(null);
    },
    onError: (error) => {
      showToast(
        "error",
        error instanceof ApiError ? error.message : "削除に失敗しました",
      );
    },
  });

  const handleSubmit = () => {
    if (isSemanticMode) {
      setSubmittedQuery(input.trim());
    } else {
      setDebouncedInput(input.trim());
    }
  };

  const handleModeChange = (next: SearchMode) => {
    setMode(next);
    setSubmittedQuery("");
  };

  const openEdit = (id: number) => {
    setDetailId(null);
    setFormState({ open: true, articleId: id });
  };

  // --- 表示データの決定 ---
  const showingSearchResults = semanticActive;
  const isLoading = showingSearchResults
    ? searchQuery.isLoading
    : listQuery.isLoading;
  const isError = showingSearchResults ? searchQuery.isError : listQuery.isError;

  const cards = showingSearchResults
    ? (searchQuery.data?.results ?? []).map((r) => ({
        article: r.article,
        score: mode === "hybrid" ? undefined : r.score,
      }))
    : (listQuery.data?.items ?? []).map((article) => ({
        article,
        score: undefined as number | undefined,
      }));

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3.5">
          <div className="flex items-center gap-2.5">
            <div className="rounded-lg bg-indigo-600 p-1.5 text-white">
              <BookOpen size={20} />
            </div>
            <div>
              <h1 className="text-lg font-bold leading-tight text-slate-900">
                TechInsight
              </h1>
              <p className="text-[11px] leading-tight text-slate-500">
                AI搭載型ナレッジベース
              </p>
            </div>
          </div>
          <button
            onClick={() => setFormState({ open: true, articleId: null })}
            className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-700"
          >
            <Plus size={16} />
            記事を投稿
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        <SearchBar
          input={input}
          onInputChange={setInput}
          mode={mode}
          onModeChange={handleModeChange}
          onSubmit={handleSubmit}
          categories={categories}
          category={category}
          onCategoryChange={setCategory}
          isSearching={searchQuery.isFetching}
        />

        <div className="mt-6">
          {/* 件数表示 */}
          {!isLoading && !isError && (
            <p className="mb-3 text-sm text-slate-500" role="status">
              {showingSearchResults
                ? `「${submittedQuery}」の検索結果 ${cards.length} 件`
                : formatTotal(listQuery.data)}
            </p>
          )}

          {isError && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center text-sm text-rose-700">
              データの取得に失敗しました。バックエンドの起動を確認してください。
            </div>
          )}

          {isLoading && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-52 animate-pulse rounded-xl border border-slate-200 bg-white p-5"
                >
                  <div className="mb-3 h-4 w-1/4 rounded bg-slate-100" />
                  <div className="mb-2 h-5 w-3/4 rounded bg-slate-200" />
                  <div className="h-16 rounded bg-slate-100" />
                </div>
              ))}
            </div>
          )}

          {!isLoading && !isError && cards.length === 0 && (
            <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-slate-300 bg-white py-16 text-slate-400">
              <SearchX size={36} />
              <p className="text-sm">
                {showingSearchResults
                  ? "該当する記事が見つかりませんでした。別の表現で試してみてください。"
                  : "記事がありません。「記事を投稿」から作成できます。"}
              </p>
            </div>
          )}

          {!isLoading && !isError && cards.length > 0 && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {cards.map(({ article, score }) => (
                <ArticleCard
                  key={article.id}
                  article={article}
                  score={score}
                  onOpen={setDetailId}
                  onEdit={openEdit}
                  onDelete={setDeleteId}
                />
              ))}
            </div>
          )}

          {!showingSearchResults && listQuery.data && (
            <div className="mt-6">
              <Pagination
                page={pageNumber}
                hasNext={Boolean(listQuery.data.next_cursor)}
                onPrev={() => setCursorStack((s) => s.slice(0, -1))}
                onNext={() => {
                  const next = listQuery.data?.next_cursor;
                  if (next) setCursorStack((s) => [...s, next]);
                }}
              />
            </div>
          )}
        </div>
      </main>

      {/* --- モーダル群 --- */}
      {detailId !== null && (
        <ArticleDetailModal
          articleId={detailId}
          onClose={() => setDetailId(null)}
          onEdit={openEdit}
          onDelete={setDeleteId}
        />
      )}

      {formState.open && (
        <ArticleFormModal
          articleId={formState.articleId}
          onClose={() => setFormState({ open: false })}
        />
      )}

      {deleteId !== null && (
        <ConfirmDialog
          title="記事の削除"
          message="この記事を削除します。この操作は取り消せません。よろしいですか？"
          confirmLabel="削除する"
          isPending={deleteMutation.isPending}
          onConfirm={() => deleteMutation.mutate(deleteId)}
          onCancel={() => setDeleteId(null)}
        />
      )}
    </div>
  );
}

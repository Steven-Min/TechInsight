"use client";

import { Search, Sparkles, Blend, Type } from "lucide-react";
import type { SearchMode } from "@/lib/types";

interface SearchBarProps {
  input: string;
  onInputChange: (value: string) => void;
  mode: SearchMode;
  onModeChange: (mode: SearchMode) => void;
  onSubmit: () => void;
  categories: string[];
  category: string;
  onCategoryChange: (category: string) => void;
  isSearching: boolean;
}

const MODES: { value: SearchMode; label: string; icon: React.ReactNode; hint: string }[] = [
  {
    value: "keyword",
    label: "キーワード",
    icon: <Type size={14} />,
    hint: "タイトル・本文の部分一致で検索",
  },
  {
    value: "semantic",
    label: "セマンティック",
    icon: <Sparkles size={14} />,
    hint: "AI が意味の近い記事を検索（自然文OK）",
  },
  {
    value: "hybrid",
    label: "ハイブリッド",
    icon: <Blend size={14} />,
    hint: "キーワードとセマンティックの結果を統合",
  },
];

export function SearchBar({
  input,
  onInputChange,
  mode,
  onModeChange,
  onSubmit,
  categories,
  category,
  onCategoryChange,
  isSearching,
}: SearchBarProps) {
  const currentMode = MODES.find((m) => m.value === mode)!;

  return (
    <div className="space-y-3">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit();
        }}
        className="flex flex-col gap-2 sm:flex-row"
      >
        <div className="relative flex-1">
          <Search
            size={18}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
          />
          <input
            type="text"
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            placeholder={
              mode === "keyword"
                ? "キーワードで絞り込み（例: PostgreSQL）"
                : "自然文で検索（例: データベースの速度を改善したい）"
            }
            className="w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-10 pr-4 text-sm shadow-sm outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
          />
        </div>
        <div className="flex gap-2">
          <select
            value={category}
            onChange={(e) => onCategoryChange(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm shadow-sm outline-none transition focus:border-indigo-500"
            aria-label="カテゴリで絞り込み"
          >
            <option value="">全カテゴリ</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={isSearching}
            className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-700 disabled:opacity-60"
          >
            {isSearching ? "検索中…" : "検索"}
          </button>
        </div>
      </form>

      <div className="flex flex-wrap items-center gap-2">
        <div className="flex rounded-lg border border-slate-200 bg-white p-0.5 shadow-sm">
          {MODES.map((m) => (
            <button
              key={m.value}
              type="button"
              onClick={() => onModeChange(m.value)}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition ${
                mode === m.value
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {m.icon}
              {m.label}
            </button>
          ))}
        </div>
        <p className="text-xs text-slate-500">{currentMode.hint}</p>
      </div>
    </div>
  );
}

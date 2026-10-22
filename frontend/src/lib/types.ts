export type SearchMode = "keyword" | "semantic" | "hybrid";

export interface ArticleListItem {
  id: number;
  title: string;
  excerpt: string;
  category: string | null;
  tags: string[];
  author: string | null;
  published_at: string | null;
  updated_at: string;
}

export interface Article {
  id: number;
  title: string;
  content: string;
  category: string | null;
  tags: string[];
  author: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * total の性質:
 * - eq: 正確な件数
 * - gte: 上限打ち切り（実際は total 件以上）
 * - approx: DB 統計による概算
 */
export type TotalRelation = "eq" | "gte" | "approx";

export interface PaginatedArticles {
  items: ArticleListItem[];
  total: number;
  total_relation: TotalRelation;
  page_size: number;
  /** 次ページ取得用カーソル。null なら最終ページ */
  next_cursor: string | null;
}

export interface SearchResultItem {
  article: ArticleListItem;
  score: number;
}

export interface SearchResponse {
  mode: SearchMode;
  query: string;
  results: SearchResultItem[];
}

export interface ArticleInput {
  title: string;
  content: string;
  category: string | null;
  tags: string[];
  author: string | null;
  published_at: string | null;
}

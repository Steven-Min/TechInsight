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

export interface PaginatedArticles {
  items: ArticleListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
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

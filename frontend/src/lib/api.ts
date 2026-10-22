import type {
  Article,
  ArticleInput,
  PaginatedArticles,
  SearchMode,
  SearchResponse,
} from "./types";

// Next.js の rewrites 経由でバックエンドへプロキシされる（CORS 不要）
const API_BASE = "/api/backend/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!res.ok) {
    let detail = `リクエストに失敗しました (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // JSON でないエラーレスポンスはそのまま
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  listArticles(params: {
    page: number;
    pageSize?: number;
    q?: string;
    category?: string;
  }): Promise<PaginatedArticles> {
    const query = new URLSearchParams({ page: String(params.page) });
    if (params.pageSize) query.set("page_size", String(params.pageSize));
    if (params.q) query.set("q", params.q);
    if (params.category) query.set("category", params.category);
    return request(`/articles?${query}`);
  },

  searchArticles(params: {
    q: string;
    mode: SearchMode;
    limit?: number;
  }): Promise<SearchResponse> {
    const query = new URLSearchParams({ q: params.q, mode: params.mode });
    if (params.limit) query.set("limit", String(params.limit));
    return request(`/articles/search?${query}`);
  },

  getArticle(id: number): Promise<Article> {
    return request(`/articles/${id}`);
  },

  listCategories(): Promise<string[]> {
    return request(`/articles/categories`);
  },

  createArticle(input: ArticleInput): Promise<Article> {
    return request(`/articles`, {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  updateArticle(id: number, input: Partial<ArticleInput>): Promise<Article> {
    return request(`/articles/${id}`, {
      method: "PATCH",
      body: JSON.stringify(input),
    });
  },

  deleteArticle(id: number): Promise<void> {
    return request(`/articles/${id}`, { method: "DELETE" });
  },
};

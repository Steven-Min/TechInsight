"use client";

import { AlertTriangle } from "lucide-react";
import { Modal } from "./modal";

interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel: string;
  isPending: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  title,
  message,
  confirmLabel,
  isPending,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <Modal title={title} onClose={onCancel} maxWidth="max-w-md">
      <div className="flex items-start gap-3">
        <div className="rounded-full bg-rose-50 p-2 text-rose-600">
          <AlertTriangle size={20} />
        </div>
        <p className="pt-1.5 text-sm leading-relaxed text-slate-600">{message}</p>
      </div>
      <div className="mt-5 flex justify-end gap-2">
        <button
          onClick={onCancel}
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
        >
          キャンセル
        </button>
        <button
          onClick={onConfirm}
          disabled={isPending}
          className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-rose-700 disabled:opacity-60"
        >
          {isPending ? "削除中…" : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}

import type { Grade } from "./types";

export type TranscriptRow = {
  key: string;
  code: string | null;
  grade: Grade;
  needsReview: boolean;
  semester: string;
  reasons: string[];
  raw: string;
  stored: boolean;
};

const object = (value: unknown): Record<string, unknown> | null =>
  value !== null && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown> : null;
const strings = (value: unknown): string[] => Array.isArray(value)
  ? value.filter((item): item is string => typeof item === "string") : [];
const numberIn = (value: unknown, max: number) =>
  typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= max
    ? value : null;

// This creates display rows only. Provisional OCR values never enter grades.
export function transcriptRows(grades: Record<string, Grade>, report: unknown): TranscriptRow[] {
  const rows: TranscriptRow[] = Object.entries(grades).map(([code, grade]) => ({
    key: `grade:${code}`, code, grade, needsReview: false, semester: "",
    reasons: [], raw: "", stored: true,
  }));
  const data = object(report);
  if (!data) return rows;
  const current = Array.isArray(data.dong_can_ra_soat);
  const candidates = current ? data.dong_can_ra_soat : data.chi_tiet;
  if (!Array.isArray(candidates)) return rows;
  const uncertain = new Set(strings(data.khong_chac));
  for (const [index, value] of candidates.entries()) {
    const item = object(value);
    if (!item) continue;
    const code = typeof item.ma === "string" && item.ma ? item.ma : null;
    if (code === "SHCVHT") continue;
    const existing = code ? rows.find((row) => row.stored && row.code === code) : undefined;
    // Legacy reports have all checked rows, but no provisional numeric scores.
    if (!current && existing && !uncertain.has(code!)) continue;
    const reasons = strings(item.ly_do);
    if (!reasons.length) reasons.push("Cần đối chiếu mã môn, điểm và học kỳ với bảng điểm gốc.");
    const semester = typeof item.hoc_ky === "string" ? item.hoc_ky : "";
    const raw = typeof item.ocr_raw === "string" ? item.ocr_raw : "";
    if (existing) {
      existing.needsReview = true;
      existing.reasons.push(...reasons);
      existing.semester = [existing.semester, semester].filter(Boolean).join(", ");
      existing.raw = [existing.raw, raw].filter(Boolean).join("\n");
      continue;
    }
    rows.push({
      key: `review:${index}`, code, needsReview: true, semester, reasons, raw, stored: false,
      grade: {
        code: code ?? "", credits: current ? numberIn(item.tc, 50) : null,
        thang10: current ? numberIn(item.thang10, 100) : null,
        letter: current && typeof item.diem_chu === "string" ? item.diem_chu : null,
      },
    });
  }
  return rows.sort((a, b) => Number(b.needsReview) - Number(a.needsReview));
}

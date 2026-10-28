"use client";

import { useEffect, useState } from "react";
import type { Course, OcrReviewChange } from "@/lib/types";
import type { OcrSemester, TranscriptRow } from "@/lib/transcript-review";

type Review = (change: OcrReviewChange) => Promise<void>;
const letters = ["A", "B+", "B", "C+", "C", "D+", "D", "F"];

export function OcrRowEditor({ row, courses, busy, available, onReview }: {
  row: TranscriptRow; courses: Course[]; busy: boolean; available: boolean; onReview: Review;
}) {
  const [code, setCode] = useState(row.code ?? "");
  const [credits, setCredits] = useState(String(row.grade.credits ?? ""));
  const [score, setScore] = useState(row.grade.thang10 == null ? "" : String(row.grade.thang10 / 10));
  const [letter, setLetter] = useState(row.grade.letter ?? "");
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  useEffect(() => {
    setCode(row.code ?? ""); setCredits(String(row.grade.credits ?? ""));
    setScore(row.grade.thang10 == null ? "" : String(row.grade.thang10 / 10));
    setLetter(row.grade.letter ?? ""); setError("");
  }, [row.code, row.grade.credits, row.grade.thang10, row.grade.letter]);
  const locked = row.code === "CC004" || row.grade.letter === "M";
  async function submit(change: OcrReviewChange) {
    try { await onReview(change); setError(""); }
    catch (e) { setError(e instanceof Error ? e.message : "Chưa duyệt được dòng này."); }
  }
  return <details className="ocr-row-editor" onToggle={(event) => setOpen(event.currentTarget.open)}>
    <summary>{row.reviewed ? "Sửa & duyệt lại" : "Sửa & duyệt"}</summary>
    {open && (!available || !row.reviewId ? <p>Bản OCR cũ thiếu dữ liệu kiểm tra lại. Hãy OCR lại PDF một lần.</p>
      : locked ? <p>Dòng miễn học cần chứng nhận hoặc xác nhận từ Phòng Đào tạo; không duyệt thành điểm số.</p>
      : <>
        <p>Đối chiếu bảng điểm gốc, sửa dữ liệu rồi duyệt dòng này.</p>
        <div className="ocr-edit-fields">
          <label>Mã học phần<select aria-label={`Mã môn rà soát ${row.key}`} value={code} disabled={busy}
            onChange={(e) => { setCode(e.target.value); const c = courses.find((c) => c.ma === e.target.value); if (c) setCredits(String(c.tin_chi)); }}>
            <option value="">Chọn học phần…</option>
            {!courses.some((c) => c.ma === code) && code && <option value={code}>{code} — chưa thuộc CTĐT</option>}
            {courses.map((c) => <option key={c.ma} value={c.ma}>{c.ma} — {c.ten}</option>)}
          </select></label>
          <label>Tín chỉ<input aria-label={`Tín chỉ rà soát ${row.key}`} type="number" min="1" max="15" step="1"
            value={credits} disabled={busy} onChange={(e) => setCredits(e.target.value)} /></label>
          <label>Điểm /10<input aria-label={`Điểm rà soát ${row.key}`} type="number" min="0" max="10" step="0.1"
            value={score} disabled={busy} onChange={(e) => setScore(e.target.value)} /></label>
          <label>Điểm chữ<select aria-label={`Điểm chữ rà soát ${row.key}`} value={letter} disabled={busy} onChange={(e) => setLetter(e.target.value)}>
            <option value="">Chọn điểm chữ…</option>{letters.map((l) => <option key={l}>{l}</option>)}
          </select></label>
        </div>
        {error && <p role="alert">{error}</p>}
        <div className="ocr-edit-actions">
          <button className="button primary" disabled={busy} onClick={() => {
            if (!code || !credits || !score || !letter || !Number.isFinite(Number(score)) ||
              Number(score) < 0 || Number(score) > 10 || Math.abs(Number(score) * 10 - Math.round(Number(score) * 10)) > 1e-6) {
              setError("Điền đủ mã môn, tín chỉ, điểm 0–10 (một chữ số thập phân) và điểm chữ."); return;
            }
            setError("");
            void submit({ action: "approve", row_id: row.reviewId!, code, credits: Number(credits),
              thang10: Math.round(Number(score) * 10), letter });
          }}>Duyệt dòng này</button>
          <button className="button outline" disabled={busy} onClick={() => void submit({ action: "exclude", row_id: row.reviewId! })}>
            Loại dòng nhận nhầm
          </button>
        </div>
        <p className="muted small">Sau khi duyệt, hệ thống kiểm tra lại cả học kỳ. Lỗi tổng hoặc dữ kiện khác chưa khớp vẫn được giữ.</p>
      </>)}
  </details>;
}

export function OcrSemesterEditor({ semesters, busy, onReview }: { semesters: OcrSemester[]; busy: boolean; onReview: Review }) {
  return <details className="ocr-semester-editor"><summary>Đối chiếu và sửa số tổng học kỳ</summary>
    <p>Sửa theo số in trên bảng điểm khi OCR đọc thiếu hoặc sai. Hệ thống kiểm tra lại với các dòng học phần.</p>
    {semesters.map((semester) => <SemesterForm key={semester.index} semester={semester} busy={busy} onReview={onReview} />)}
  </details>;
}

function SemesterForm({ semester, busy, onReview }: { semester: OcrSemester; busy: boolean; onReview: Review }) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const signature = JSON.stringify(semester.totals);
  useEffect(() => { setValues(Object.fromEntries(Object.entries(JSON.parse(signature)).map(([k, v]) => [k, v == null ? "" : String(v)]))); }, [signature]);
  const labels: Record<string, string> = { tong_dk: "Tổng TC đăng ký", dtbchk: "ĐTB học kỳ /4", tc_tich_luy: "TC tích lũy", dtbctl: "ĐTB tích lũy /4" };
  return <fieldset><legend>{semester.name}</legend><div className="ocr-edit-fields">
    {Object.entries(labels).map(([key, label]) => <label key={key}>{label}<input aria-label={`${label} ${semester.name}`}
      type="number" min="0" max={key.startsWith("dtb") ? "4" : "1000"} step={key.startsWith("dtb") ? "0.01" : "1"}
      disabled={busy} value={values[key] ?? ""} onChange={(e) => setValues({ ...values, [key]: e.target.value })} /></label>)}
    </div>{error && <p role="alert">{error}</p>}<button className="button outline" disabled={busy} onClick={async () => {
      try { await onReview({ action: "semester", semester_index: semester.index,
        totals: Object.fromEntries(Object.entries(values).filter(([, value]) => value !== "").map(([key, value]) => [key, Number(value)])) }); setError(""); }
      catch (e) { setError(e instanceof Error ? e.message : "Chưa duyệt được số tổng."); }
    }}>Duyệt số tổng {semester.name}</button>
  </fieldset>;
}

import { expect, test } from "vitest";
import { transcriptRows } from "../lib/transcript-review";

test("uncertain OCR scores appear as warning rows without changing student facts", () => {
  const grades = { CT100: { code: "CT100", credits: 2, thang10: 92, letter: "A" } };
  const before = structuredClone(grades);
  const rows = transcriptRows(grades, { dong_can_ra_soat: [
    { ma: "CT101", tc: 4, thang10: 97, diem_chu: "A", hoc_ky: "HK2",
      ly_do: ["Độ tin cậy thấp"], ocr_raw: "CT101 4 9.7 A" },
  ] });
  expect(rows.map((r) => [r.code, r.needsReview])).toEqual([["CT101", true], ["CT100", false]]);
  expect(rows[0].grade.thang10).toBe(97);
  expect(rows[0].stored).toBe(false);
  expect(grades).toEqual(before);
});

test("missing scores stay blank, unknown codes and repeated attempts remain visible", () => {
  const rows = transcriptRows({}, { dong_can_ra_soat: [
    { ma: null, tc: null, thang10: null },
    { ma: "CT101", hoc_ky: "HK1", thang10: 30 },
    { ma: "CT101", hoc_ky: "HK2", thang10: null },
    { ma: "TC025", thang10: 92, diem_chu: "A" },
  ] });
  expect(rows).toHaveLength(4);
  expect(new Set(rows.map((r) => r.key)).size).toBe(4);
  expect(rows[0].grade.thang10).toBeNull();
  expect(rows[2].grade.thang10).toBeNull();
  expect(rows.every((r) => r.needsReview)).toBe(true);
});

test("legacy reports do not infer numeric grades from OCR text", () => {
  const rows = transcriptRows({}, { khong_chac: ["CT101", "CT178"], chi_tiet: [
    { ma: "CT101", hoc_ky: "HK2", ocr_raw: "CT101 4 9.7 A" },
  ] });
  expect(rows).toHaveLength(1); // CT178 was inferred, never observed.
  expect(rows[0].grade.thang10).toBeNull();
});

test("manual edits do not silently clear an OCR warning", () => {
  const rows = transcriptRows({ CT101: { code: "CT101", thang10: 86 } }, {
    dong_can_ra_soat: [{ ma: "CT101", thang10: 97, ly_do: ["Cần đối chiếu"] }],
  });
  expect(rows).toHaveLength(1);
  expect(rows[0].grade.thang10).toBe(86);
  expect(rows[0].needsReview).toBe(true);
});

test("invalid imported report values cannot crash the table or become scores", () => {
  expect(transcriptRows({}, { dong_can_ra_soat: [null, "bad", { thang10: 900, ly_do: 7 }] })[0].grade.thang10).toBeNull();
  expect(transcriptRows({}, { dong_can_ra_soat: "bad" })).toEqual([]);
});

test("approved and pending rows retain stable IDs for server review", () => {
  const rows = transcriptRows({ CT101: { code: "CT101", thang10: 97, reviewed_by_user: true } }, {
    tai_lieu_ocr: { hoc_ky: [{ ten: "HK1", dong: [{ ma: "CT101", thop: 9.7, row_id: "kept-id" }] }] },
    dong_can_ra_soat: [{ ma: "CT100", id: "other-id", da_duyet: true }],
  });
  expect(rows.find((r) => r.code === "CT101")?.reviewId).toBe("kept-id");
  expect(rows.find((r) => r.code === "CT100")?.reviewed).toBe(true);
});

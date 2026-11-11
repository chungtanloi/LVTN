import { expect, test } from "vitest";
import { countsInStats, creditsForNewCourse } from "../lib/courses";

const courses = [
  { ma: "CT101", tin_chi: 4, dieu_kien: null },
  { ma: "QP010E", tin_chi: 2, dieu_kien: "gdqp" },
];
const recognition = [
  { ma: "ML010", ten: "Những nguyên lý cơ bản của Chủ nghĩa Mác-Lênin 2", tin_chi_van_ban: 3, nguon: "QĐ5339 Đ3 k9" },
  { ma: "ML006", ten: "Tư tưởng Hồ Chí Minh", tin_chi_van_ban: null, nguon: "QĐ5339 Đ3 k9" },
];

test("old LLCT courses kept only for recognition never enter descriptive credit/GPA stats", () => {
  const map = new Map(courses.map((c) => [c.ma, c]));
  expect(["CT101", "QP010E", "ML010", "XX999"].filter((code) => countsInStats(code, map))).toEqual(["CT101"]);
});

test("curriculum courses take credits from the curriculum", () => {
  expect(creditsForNewCourse("CT101", courses, recognition, "")).toEqual({ credits: 4 });
});

test("recognition-only courses need explicit whole credits, never a guessed default", () => {
  expect(creditsForNewCourse("ML010", courses, recognition, "3")).toEqual({ credits: 3 });
  for (const input of ["", "0", "2.5", "-1", "11", "abc"])
    expect(creditsForNewCourse("ML006", courses, recognition, input)).toHaveProperty("error");
  expect(creditsForNewCourse("XX999", courses, recognition, "3")).toHaveProperty("error");
});

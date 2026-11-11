/** Course helpers shared by the profile editor and tests (C26). */
export type RecognitionCourse = {
  ma: string;
  ten: string;
  tin_chi_van_ban: number | null;
  nguon: string;
};
type CurriculumCourse = { ma: string; tin_chi: number; dieu_kien?: string | null };

/** Descriptive stats count only curriculum, non-condition courses. Old LLCT courses (recognition only) never count. */
export function countsInStats(code: string, courseMap: Map<string, CurriculumCourse>) {
  const course = courseMap.get(code);
  return Boolean(course) && !course!.dieu_kien;
}

/** Credits for a newly added grade: curriculum value, or an explicit whole number for recognition-only courses. */
export function creditsForNewCourse(
  code: string,
  courses: CurriculumCourse[],
  recognition: RecognitionCourse[],
  input: string,
): { credits: number } | { error: string } {
  const course = courses.find((c) => c.ma === code);
  if (course) return { credits: course.tin_chi };
  if (!recognition.some((c) => c.ma === code)) return { error: "Học phần không thuộc CTĐT CNTT K49." };
  const credits = Number(input);
  if (input.trim() === "" || !Number.isInteger(credits) || credits < 1 || credits > 10)
    return { error: `${code}: nhập số tín chỉ (số nguyên 1–10) theo bảng điểm.` };
  return { credits };
}

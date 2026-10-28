export type Grade = {
  code: string;
  credits?: number | null;
  thang10?: number | null;
  letter?: string | null;
  diem?: string | null;
  status?: string;
  confidence?: number | null;
  [key: string]: unknown;
};
export type Profile = {
  student_id: string;
  major: string;
  cohort: string;
  ctdt?: string;
  grades: Record<string, Grade>;
  meta?: Record<string, unknown>;
  [key: string]: unknown;
};
export type Course = {
  ma: string;
  ten: string;
  tin_chi: number;
  cot: string;
  khoi: string;
  dieu_kien?: string | null;
  tien_quyet: string[];
  song_hanh: string[];
  hk?: string | null;
};
export type ProofStep = {
  atom: string;
  rule_id?: string;
  source?: { van_ban?: string; dieu?: number; khoan?: string; trich?: string };
  facts?: string[];
};
export type Advice = {
  verdict: string;
  claim?: string;
  explanation_vi?: string;
  missing_facts?: string[];
  can_bo_sung?: { bien: string; hoi: string }[];
  mau_thuan?: string[];
  certificate?: { proof?: { steps?: ProofStep[] }; [key: string]: unknown };
  nguon?: {
    passage_id: string;
    dia_chi?: string;
    trang?: number | string;
    trich?: string;
    [key: string]: unknown;
  }[];
  de_xuat?: Recommendation;
  kb_version?: string;
  reason?: string;
};
export type Recommendation = {
  dang_ky?: {
    ma: string;
    ten: string;
    tc: number;
    ly_do: string;
    chung_chi: unknown[];
  }[];
  tong_tc?: number;
  can_xac_minh?: { ma?: string; ly_do: string }[];
  [key: string]: unknown;
};
export type Message = {
  id: string;
  question: string;
  result: Advice;
  createdAt: number;
  revision: number;
};
export type Demo = { id: string; name: string; profile: Profile };
export type OcrResult = {
  profile: Profile;
  report: {
    tong_dong?: number;
    hoc_ky_lech?: string[];
    khong_chac?: string[];
    dong_an?: number;
    can_hoi?: string[];
    [key: string]: unknown;
  };
  needs_review: boolean;
};
export type Tab =
  | "overview"
  | "transcript"
  | "chat"
  | "plan"
  | "sources"
  | "history"
  | "settings";

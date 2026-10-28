"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { SignInButton, UserButton, useAuth } from "@clerk/nextjs";
import { useAction, useConvexAuth, useMutation, useQuery } from "convex/react";
import { anyApi } from "convex/server";
import {
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  AlertTriangle,
  BookOpen,
  Check,
  CheckCheck,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  ClipboardList,
  FileCheck2,
  FileJson,
  GraduationCap,
  History,
  LayoutDashboard,
  LoaderCircle,
  Menu,
  MessageSquareText,
  Plus,
  Search,
  Send,
  Settings2,
  ShieldCheck,
  Sparkles,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import type {
  Advice,
  Course,
  Demo,
  Grade,
  Message,
  OcrResult,
  Profile,
  Recommendation,
  Tab,
} from "@/lib/types";
import { transcriptRows } from "@/lib/transcript-review";

type Data = {
  profile: Profile | null;
  revision: number;
  messages: Message[];
  courses: Course[];
  demos: Demo[];
  ocr?: OcrResult;
  ocrStatus?: string;
};
type Operations = {
  save: (profile: Profile, consent: boolean) => Promise<void>;
  ask: (question: string) => Promise<Message>;
  lookup: (
    question: string,
  ) => Promise<{ passages: Record<string, unknown>[] }>;
  recommend: (semester: number) => Promise<Recommendation>;
  ocr: (files: File[], consent: boolean) => Promise<OcrResult | null>;
  erase: () => Promise<void>;
};
const nav: { id: Tab; label: string; icon: typeof LayoutDashboard }[] = [
  { id: "overview", label: "Tổng quan", icon: LayoutDashboard },
  { id: "transcript", label: "Hồ sơ & bảng điểm", icon: ClipboardList },
  { id: "chat", label: "Tư vấn học vụ", icon: MessageSquareText },
  { id: "plan", label: "Kế hoạch học tập", icon: GraduationCap },
  { id: "sources", label: "Kho quy chế", icon: BookOpen },
  { id: "history", label: "Lịch sử tư vấn", icon: History },
];
const questions = [
  "Em đủ điều kiện tốt nghiệp chưa?",
  "Em có đủ điều kiện làm luận văn tốt nghiệp không?",
  "Em có được đăng ký CT180 không?",
  "Học kỳ 1 em nên đăng ký gì?",
];
const points: Record<string, number> = {
  A: 4,
  "B+": 3.5,
  B: 3,
  "C+": 2.5,
  C: 2,
  "D+": 1.5,
  D: 1,
  F: 0,
};
const emptyProfile: Profile = {
  student_id: "sv_cpa2",
  major: "cntt",
  cohort: "K49",
  ctdt: "cntt_k49",
  grades: {},
};
const labelVerdict: Record<string, string> = {
  TRUE: "Đã xác định",
  FALSE: "Chưa đáp ứng",
  UNKNOWN: "Cần thêm thông tin",
  BLOCKED: "Hậu kiểm đã chặn",
  UNSAT: "Hồ sơ mâu thuẫn",
  MAU_THUAN: "Hồ sơ mâu thuẫn",
  DA_HOAN_THANH: "Đã hoàn thành",
};

async function demoRequest(operation: string, body?: unknown) {
  const response = await fetch(`/api/demo/${operation}`, {
    method: body === undefined ? "GET" : "POST",
    headers:
      body instanceof FormData ? {} : { "Content-Type": "application/json" },
    body:
      body === undefined
        ? undefined
        : body instanceof FormData
          ? body
          : JSON.stringify(body),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error ?? "Yêu cầu chưa thành công.");
  return result;
}

export function Workspace({
  connected,
  demo,
}: {
  connected: boolean;
  demo: boolean;
}) {
  if (connected) return <CloudGate />;
  if (demo) return <DemoWorkspace />;
  return (
    <div className="setup-page">
      <Brand />
      <div className="setup-card">
        <ShieldCheck size={38} />
        <h1>CPA² đang chờ cấu hình</h1>
        <p>
          Kết nối Clerk, Convex và dịch vụ Python để mở không gian tư vấn học
          vụ.
        </p>
        <p>
          Để chạy thử với hồ sơ giả lập trên máy cá nhân, dùng lệnh trong README
          của CPA2_App.
        </p>
      </div>
    </div>
  );
}

function CloudGate() {
  const { isLoaded, isSignedIn } = useAuth();
  const { isAuthenticated, isLoading } = useConvexAuth();
  if (!isLoaded || (isSignedIn && isLoading)) return <Loading />;
  if (!isSignedIn)
    return (
      <div className="login-page">
        <div className="login-copy">
          <Brand />
          <span className="eyebrow light">
            CERTIFIED PERSONALIZED ACADEMIC ADVISING
          </span>
          <h1>
            Hiểu hành trình học tập.
            <br />
            <em>Vững bước tiếp theo.</em>
          </h1>
          <p>
            Mỗi lời tư vấn đều có cơ sở. Khám phá kế hoạch học tập của bạn với
            CPA².
          </p>
          <div className="login-facts">
            <ShieldCheck /> Kết luận có chứng minh <span>·</span> CNTT K49
          </div>
        </div>
        <div className="login-panel">
          <div className="login-card">
            <GraduationCap size={40} />
            <h2>Chào mừng đến CPA²</h2>
            <p>Đăng nhập để quản lý hồ sơ và nhận tư vấn học vụ cá nhân hóa.</p>
            <SignInButton mode="modal">
              <button className="button primary full">
                Đăng nhập để bắt đầu <ArrowRight size={17} />
              </button>
            </SignInButton>
            <small>Đại học Cần Thơ · Công nghệ thông tin K49</small>
          </div>
        </div>
      </div>
    );
  if (!isAuthenticated)
    return (
      <div className="setup-page">
        <Brand />
        <p>
          Đã đăng nhập Clerk nhưng chưa xác thực được Convex. Kiểm tra JWT
          issuer và cấu hình auth của Convex.
        </p>
        <UserButton />
      </div>
    );
  return <CloudWorkspace />;
}

function Loading() {
  return (
    <div className="loading-page">
      <Brand />
      <LoaderCircle className="spin" />
      <p>Đang mở không gian học tập…</p>
    </div>
  );
}
function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark">
        <GraduationCap size={23} strokeWidth={1.8} />
      </span>
      <span>
        CPA<sup>2</sup>
        <small>ACADEMIC ADVISING</small>
      </span>
    </div>
  );
}

function DemoWorkspace() {
  const [data, setData] = useState<Data>({
    profile: null,
    revision: 0,
    messages: [],
    courses: [],
    demos: [],
  });
  const [error, setError] = useState("");
  const initialize = useCallback(async () => {
    setError("");
    try {
      const [catalog, demos] = await Promise.all([
        demoRequest("catalog"),
        demoRequest("profiles"),
      ]);
      setData((current) => ({
        ...current,
        courses: catalog.courses,
        demos,
        profile: current.profile ?? demos[0]?.profile,
        revision: current.revision || 1,
      }));
    } catch (e) {
      setError(message(e));
    }
  }, []);
  useEffect(() => {
    void initialize();
  }, [initialize]);
  const ops: Operations = {
    save: async (profile) => {
      const result = await demoRequest("validate", { profile });
      setData((current) => ({
        ...current,
        profile: result.profile,
        revision: current.revision + 1,
      }));
    },
    ask: async (question) => {
      const result = await demoRequest("advice", {
        question,
        profile: data.profile,
      });
      const entry = {
        id: crypto.randomUUID(),
        question,
        result,
        createdAt: Date.now(),
        revision: data.revision,
      };
      setData((current) => ({
        ...current,
        messages: [entry, ...current.messages],
      }));
      return entry;
    },
    lookup: (question) => demoRequest("lookup", { question }),
    recommend: (semester) =>
      demoRequest("recommendations", { semester, profile: data.profile }),
    ocr: async (files) => {
      const form = new FormData();
      files.forEach((file) => form.append("files", file));
      return await demoRequest("ocr", form);
    },
    erase: async () =>
      setData((current) => ({
        ...current,
        profile: null,
        messages: [],
        revision: 0,
        ocr: undefined,
      })),
  };
  return (
    <Shell
      data={data}
      ops={ops}
      demo
      connectionError={error}
      retry={initialize}
    />
  );
}

function CloudWorkspace() {
  const state = useQuery(anyApi.cpa2.state, {});
  const configure = useAction(anyApi.cpa2.configuration);
  const save = useAction(anyApi.cpa2.saveProfile),
    ask = useAction(anyApi.cpa2.advise),
    lookup = useAction(anyApi.cpa2.lookup),
    recommend = useAction(anyApi.cpa2.recommend);
  const uploadUrl = useMutation(anyApi.cpa2.uploadUrl),
    startOcr = useMutation(anyApi.cpa2.startOcr),
    erase = useMutation(anyApi.cpa2.eraseData);
  const [catalog, setCatalog] = useState<{ courses: Course[]; demos: Demo[] }>({
    courses: [],
    demos: [],
  });
  const [error, setError] = useState("");
  const [ocrId, setOcrId] = useState<string | null>(null);
  const initialize = useCallback(async () => {
    try {
      const config = await configure({});
      setCatalog({ courses: config.catalog.courses, demos: config.demos });
      setError("");
    } catch (e) {
      setError(message(e));
    }
  }, [configure]);
  useEffect(() => {
    void initialize();
  }, [initialize]);
  if (state === undefined) return <Loading />;
  const upload = state.uploads.find(
    (item: { _id: string }) => item._id === ocrId,
  );
  const data: Data = {
    profile: state.profile,
    revision: state.revision,
    messages: state.messages,
    ...catalog,
    ocr: upload?.result,
    ocrStatus: upload?.status === "error" ? upload.error : upload?.status,
  };
  const ops: Operations = {
    save: async (profile, consent) => {
      await save({ profile, consent });
    },
    ask: async (question) => await ask({ question }),
    lookup: async (question) => await lookup({ question }),
    recommend: async (semester) => await recommend({ semester }),
    ocr: async (files, consent) => {
      if (
        !files.length ||
        files.length > 4 ||
        files.reduce((total, file) => total + file.size, 0) > 20 * 1024 * 1024
      )
        throw new Error("Chọn PDF hoặc ảnh, tổng tối đa 4 trang và 20 MB.");
      const storageIds = [];
      for (const file of files) {
        const url = await uploadUrl({ consent });
        const response = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": file.type },
          body: file,
        });
        if (!response.ok) throw new Error("Tải bảng điểm chưa thành công.");
        const { storageId } = await response.json();
        storageIds.push(storageId);
      }
      setOcrId(await startOcr({ storageIds, consent }));
      return null;
    },
    erase: async () => {
      await erase({});
      setOcrId(null);
    },
  };
  return (
    <Shell
      data={data}
      ops={ops}
      demo={false}
      connectionError={error}
      retry={initialize}
    />
  );
}

function message(error: unknown) {
  return error instanceof Error
    ? error.message
    : "Có lỗi xảy ra. Vui lòng thử lại.";
}
function pretty(value: unknown) {
  return JSON.stringify(value, null, 2);
}
function download(name: string, value: unknown) {
  const url = URL.createObjectURL(
    new Blob([pretty(value)], { type: "application/json;charset=utf-8" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}
function gradeLetter(grade: Grade) {
  if (grade.letter) return grade.letter;
  if (grade.diem) return grade.diem;
  if (grade.thang10 == null) return "?";
  return (
    ([
      [90, "A"],
      [80, "B+"],
      [70, "B"],
      [65, "C+"],
      [55, "C"],
      [50, "D+"],
      [40, "D"],
      [0, "F"],
    ].find(([minimum]) => grade.thang10! >= Number(minimum))?.[1] as string) ??
    "?"
  );
}

function Shell({
  data,
  ops,
  demo,
  connectionError,
  retry,
}: {
  data: Data;
  ops: Operations;
  demo: boolean;
  connectionError: string;
  retry: () => Promise<void>;
}) {
  const [tab, setTab] = useState<Tab>("overview"),
    [mobile, setMobile] = useState(false);
  const [busy, setBusy] = useState(""),
    [notice, setNotice] = useState(""),
    [error, setError] = useState("");
  const [question, setQuestion] = useState(""),
    [active, setActive] = useState<Message | null>(null),
    [proof, setProof] = useState<Advice | null>(null);
  const [draft, setDraft] = useState<Profile>(data.profile ?? emptyProfile),
    [raw, setRaw] = useState(pretty(data.profile ?? emptyProfile));
  const [consent, setConsent] = useState(false),
    [reviewed, setReviewed] = useState(false),
    [ocrResult, setOcrResult] = useState<OcrResult | null>(null);
  const [filter, setFilter] = useState(""),
    [courseCode, setCourseCode] = useState(""),
    [score, setScore] = useState("");
  const [semester, setSemester] = useState(1),
    [plan, setPlan] = useState<Recommendation | null>(null);
  const [sourceQuestion, setSourceQuestion] = useState(""),
    [passages, setPassages] = useState<Record<string, unknown>[]>([]),
    [searched, setSearched] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const value = data.profile ?? emptyProfile;
    setDraft(value);
    setRaw(pretty(value));
    setPlan(null);
  }, [data.profile]);
  useEffect(() => {
    if (data.ocr) {
      setOcrResult(data.ocr);
      setDraft(data.ocr.profile);
      setRaw(pretty(data.ocr.profile));
      setTab("transcript");
      setReviewed(false);
    }
  }, [data.ocr]);
  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [active, busy]);
  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(() => setNotice(""), 5000);
    return () => clearTimeout(timer);
  }, [notice]);
  const go = (next: Tab) => {
    setTab(next);
    setMobile(false);
    setError("");
    window.scrollTo(0, 0);
  };
  async function run(name: string, action: () => Promise<void>) {
    if (busy) return;
    setBusy(name);
    setError("");
    try {
      await action();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy("");
    }
  }
  async function send(text: string) {
    if (!text.trim()) return;
    go("chat");
    setQuestion("");
    await run("ask", async () => {
      const result = await ops.ask(text.trim());
      setActive(result);
    });
  }
  function updateDraft(next: Profile) {
    setDraft(next);
    setRaw(pretty(next));
  }
  async function save() {
    await run("save", async () => {
      const candidate = JSON.parse(raw) as Profile;
      if (candidate.meta?.nguon === "ocr") {
        const report =
          ocrResult?.report ??
          (candidate.meta.ocr_report as OcrResult["report"] | undefined);
        if (
          !reviewed ||
          !report ||
          (report.khong_chac?.length ?? 0) > 0 ||
          (report.dong_an ?? 0) > 0 ||
          (report.can_hoi?.length ?? 0) > 0 ||
          ["hoc_ky_lech", "can_xac_nhan", "ngoai_ctdt", "khai_bao_loi", "dong_can_ra_soat"].some(
            (key) => Array.isArray(report[key]) && report[key].length > 0,
          )
        )
          throw new Error(
            "OCR vẫn có dữ kiện chưa chắc. Hãy nhập lại hồ sơ đầy đủ từ bảng điểm gốc bằng biểu mẫu hoặc JSON; hệ thống chưa tự xác minh các dòng này.",
          );
        candidate.meta = {
          ...candidate.meta,
          ocr_pending: false,
          reviewed_by_user: true,
        };
      }
      await ops.save(candidate, consent);
      setOcrResult(null);
      setNotice("Đã lưu hồ sơ. Kết quả tư vấn mới sẽ dùng phiên bản này.");
    });
  }
  const profile = data.profile;
  const grades = Object.entries(profile?.grades ?? {});
  const courseMap = new Map(data.courses.map((course) => [course.ma, course]));
  const counted = grades.filter(
    ([code, grade]) =>
      !courseMap.get(code)?.dieu_kien &&
      points[gradeLetter(grade)] !== undefined,
  );
  const passedCredits = counted.reduce(
    (sum, [, grade]) =>
      sum + (points[gradeLetter(grade)] > 0 ? (grade.credits ?? 0) : 0),
    0,
  );
  const gradedCredits = counted.reduce(
    (sum, [, grade]) => sum + (grade.credits ?? 0),
    0,
  );
  const gpa = gradedCredits
    ? counted.reduce(
        (sum, [, grade]) =>
          sum + points[gradeLetter(grade)] * (grade.credits ?? 0),
        0,
      ) / gradedCredits
    : null;
  const missing = [
    "xac_nhan_ky_luat_sach",
    "da_hoc_nam2",
    "tc_cong_nhan",
    "tc_diem_f",
    "ky_luat_canh_cao_cap_truong",
  ].filter((key) => profile?.[key] == null);
  const allTranscriptRows = transcriptRows(
    draft.grades,
    ocrResult?.report ?? draft.meta?.ocr_report,
  );
  const reviewCount = allTranscriptRows.filter((row) => row.needsReview).length;
  const shownGrades = allTranscriptRows.filter((row) =>
    `${row.code ?? ""} ${courseMap.get(row.code ?? "")?.ten ?? ""} ${row.semester} ${row.raw}`
      .toLocaleLowerCase("vi")
      .includes(filter.toLocaleLowerCase("vi")),
  );
  const latest = active ?? data.messages[0];
  const title = nav.find((item) => item.id === tab)?.label ?? "Cài đặt";

  return (
    <div className="app-shell">
      {mobile && (
        <button
          className="sidebar-backdrop"
          aria-label="Đóng menu"
          onClick={() => setMobile(false)}
        />
      )}
      <aside className={`sidebar ${mobile ? "is-open" : ""}`}>
        <Brand />
        <div className="workspace-label">KHÔNG GIAN HỌC TẬP</div>
        <nav aria-label="Điều hướng chính">
          {nav.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${tab === item.id ? "active" : ""}`}
              onClick={() => go(item.id)}
            >
              <item.icon size={19} />
              <span>{item.label}</span>
              {item.id === "chat" && <span className="nav-new">CPA²</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-guide">
          <div className="guide-icon">
            <ShieldCheck size={22} />
          </div>
          <h3>Tư vấn có cơ sở.</h3>
          <p>Mỗi kết luận đều được kiểm tra và truy về nguồn quy chế.</p>
          <button onClick={() => go("sources")}>
            Khám phá cách hoạt động <ArrowUpRight size={15} />
          </button>
        </div>
        <div className="sidebar-bottom">
          <button
            className={`nav-item ${tab === "settings" ? "active" : ""}`}
            onClick={() => go("settings")}
          >
            <Settings2 size={19} /> Cài đặt & dữ liệu
          </button>
          <div className="sidebar-user">
            <span className="avatar">{demo ? "SV" : <UserButton />}</span>
            <div>
              <strong>
                {demo ? "Sinh viên trải nghiệm" : "Tài khoản của bạn"}
              </strong>
              <small>
                {demo
                  ? "Hồ sơ giả lập · phiên hiện tại"
                  : "Đã đăng nhập an toàn"}
              </small>
            </div>
            {demo && <span className="online-dot" />}
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="icon-button mobile-toggle"
              aria-label="Mở menu"
              onClick={() => setMobile(true)}
            >
              <Menu size={21} />
            </button>
            <span>Không gian học tập</span>
            <ChevronRight size={14} />
            <strong>{title}</strong>
          </div>
          <div className="topbar-right">
            <span className="scope-tag">
              <span className="online-dot" /> CNTT · K49
            </span>
            <span className="top-divider" />
            <span className="mode-tag">
              {demo ? "Bản demo cục bộ" : "Không gian cá nhân"}
            </span>
          </div>
        </header>
        <main className={`content ${tab === "chat" ? "chat-content" : ""}`}>
          {(connectionError || error) && (
            <div role="alert" className="alert error">
              <CircleHelp size={19} />
              <span>{error || connectionError}</span>
              {connectionError && (
                <button onClick={() => void retry()}>Thử lại</button>
              )}
              <button
                className="icon-button"
                aria-label="Đóng thông báo lỗi"
                onClick={() => setError("")}
              >
                <X size={16} />
              </button>
            </div>
          )}
          {notice && (
            <div role="status" className="toast">
              <CheckCheck size={18} />
              {notice}
            </div>
          )}

          {tab === "overview" && (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">HÀNH TRÌNH CỦA BẠN</div>
                  <h1>
                    Học tập có định hướng<span className="heading-dot">.</span>
                  </h1>
                  <p>Một góc nhìn rõ ràng hơn cho những bước tiếp theo.</p>
                </div>
                <button
                  className="button outline"
                  onClick={() => go("transcript")}
                >
                  <Upload size={16} /> Cập nhật bảng điểm
                </button>
              </div>
              <section className="hero">
                <div className="hero-copy">
                  <span className="hero-badge">
                    <Sparkles size={13} /> TRỢ LÝ HỌC VỤ CPA²
                  </span>
                  <h2>
                    Mỗi quyết định học tập,
                    <br />
                    đều có <em>cơ sở vững vàng.</em>
                  </h2>
                  <p>
                    Kiểm tra điều kiện, tìm học phần phù hợp và hiểu rõ
                    <br className="desktop-break" /> quy chế — dựa trên chính hồ
                    sơ của bạn.
                  </p>
                  <button className="button cream" onClick={() => go("chat")}>
                    Bắt đầu tư vấn <ArrowUpRight size={17} />
                  </button>
                </div>
                <div className="hero-visual" aria-hidden="true">
                  <div className="orbit orbit-one" />
                  <div className="orbit orbit-two" />
                  <div className="orbit orbit-three" />
                  <span className="orbit-spark s1">✦</span>
                  <span className="orbit-spark s2">✦</span>
                  <div className="floating-card card-proof">
                    <span className="mini-icon green">
                      <ShieldCheck size={19} />
                    </span>
                    <div>
                      <strong>Kết luận có chứng minh</strong>
                      <small>Minh bạch từ dữ kiện đến quy chế</small>
                    </div>
                    <Check size={15} />
                  </div>
                  <div className="hero-center">
                    <GraduationCap size={53} strokeWidth={1.25} />
                  </div>
                  <div className="floating-card card-source">
                    <span className="mini-icon peach">
                      <FileCheck2 size={18} />
                    </span>
                    <div>
                      <strong>Truy về nguồn gốc</strong>
                      <small>Quy chế · Điều · Khoản</small>
                    </div>
                  </div>
                </div>
              </section>
              <div className="stats-grid">
                <Stat
                  label="Tín chỉ học phần đạt"
                  value={String(passedCredits)}
                  suffix="TC"
                  icon={BookOpen}
                  note="Theo điểm đã nhập, trừ HP điều kiện"
                  color="blue"
                />
                <Stat
                  label="Điểm trung bình"
                  value={gpa === null ? "—" : gpa.toFixed(2)}
                  suffix="/ 4.0"
                  icon={GraduationCap}
                  note="Ước tính từ các học phần đã nhập"
                  color="purple"
                />
                <Stat
                  label="Học phần trong hồ sơ"
                  value={String(grades.length)}
                  suffix="HP"
                  icon={ClipboardList}
                  note={
                    profile
                      ? `Phiên bản hồ sơ ${data.revision}`
                      : "Chưa có hồ sơ được lưu"
                  }
                  color="orange"
                />
                <Stat
                  label="Lượt tư vấn đã lưu"
                  value={String(data.messages.length)}
                  suffix="lượt"
                  icon={MessageSquareText}
                  note={
                    demo
                      ? "Trong phiên trải nghiệm hiện tại"
                      : "Có thể xem lại trong lịch sử"
                  }
                  color="green"
                />
              </div>
              <div className="overview-grid">
                <section className="panel progress-panel">
                  <div className="panel-heading">
                    <h2>Bức tranh học tập</h2>
                    <span className="subtle-tag">CTĐT CNTT K49</span>
                  </div>
                  <div className="progress-body">
                    <div
                      className="donut"
                      style={
                        {
                          "--progress": `${Math.min(100, (passedCredits / 161) * 100)}%`,
                        } as React.CSSProperties
                      }
                    >
                      <div>
                        <strong>
                          {passedCredits}
                          <small>/ 161 TC</small>
                        </strong>
                        <span>HP có điểm đạt</span>
                      </div>
                    </div>
                    <div className="block-progress">
                      {[
                        { name: "Đại cương", key: "dai_cuong", target: 56 },
                        { name: "Cơ sở ngành", key: "co_so_nganh", target: 46 },
                        {
                          name: "Chuyên ngành",
                          key: "chuyen_nganh",
                          target: 59,
                        },
                      ].map((block) => {
                        const total = counted.reduce(
                          (sum, [code, grade]) =>
                            sum +
                            (courseMap.get(code)?.khoi === block.key &&
                            points[gradeLetter(grade)] > 0
                              ? (grade.credits ?? 0)
                              : 0),
                          0,
                        );
                        return (
                          <div className="progress-row" key={block.key}>
                            <div>
                              <span>{block.name}</span>
                              <strong>
                                {total}
                                <small> / {block.target} TC</small>
                              </strong>
                            </div>
                            <div className="progress-track">
                              <span
                                style={{
                                  width: `${Math.min(100, (total / block.target) * 100)}%`,
                                }}
                              />
                            </div>
                          </div>
                        );
                      })}
                      <p className="chart-note">
                        Thống kê mô tả; kết luận tốt nghiệp còn xét nhóm tự
                        chọn, miễn và các điều kiện khác.
                      </p>
                    </div>
                  </div>
                </section>
                <section className="panel quick-panel">
                  <div className="panel-heading">
                    <h2>Bạn đang băn khoăn?</h2>
                    <span className="mini-icon light-blue">
                      <Sparkles size={16} />
                    </span>
                  </div>
                  <p className="muted small">
                    Bắt đầu từ một câu hỏi quen thuộc.
                  </p>
                  <div className="quick-questions">
                    {questions.slice(0, 3).map((text, index) => (
                      <button
                        key={text}
                        disabled={!profile || !!busy}
                        onClick={() => void send(text)}
                      >
                        <span className={`question-number n${index}`}>
                          {["01", "02", "03"][index]}
                        </span>
                        <span>{text}</span>
                        <ArrowUpRight size={16} />
                      </button>
                    ))}
                  </div>
                  <button className="text-link" onClick={() => go("chat")}>
                    Mở không gian tư vấn <ArrowRight size={15} />
                  </button>
                </section>
              </div>
              <div className="overview-grid bottom-grid">
                <section className="panel">
                  <div className="panel-heading">
                    <h2>Hồ sơ của bạn</h2>
                    <button
                      className="text-link"
                      onClick={() => go("transcript")}
                    >
                      Xem hồ sơ <ArrowRight size={14} />
                    </button>
                  </div>
                  <div className="profile-summary">
                    <div className="profile-badge">
                      <GraduationCap size={27} />
                    </div>
                    <div>
                      <h3>Công nghệ thông tin</h3>
                      <p>
                        Đại học Cần Thơ <span>·</span> Khóa 49
                      </p>
                      <span className="subtle-tag">
                        {profile?.student_id ?? "Chưa tạo hồ sơ"}
                      </span>
                    </div>
                  </div>
                  <div
                    className={`inline-note ${missing.length ? "" : "success"}`}
                  >
                    <CircleHelp size={17} />
                    <span>
                      {!profile
                        ? "Thêm bảng điểm để nhận tư vấn cá nhân hóa."
                        : missing.length
                          ? `Còn ${missing.length} dữ kiện bổ sung giúp kết luận rõ hơn.`
                          : "Các dữ kiện bổ sung chính đã được khai báo."}
                    </span>
                    <button onClick={() => go("transcript")}>Cập nhật</button>
                  </div>
                </section>
                <section className="panel">
                  <div className="panel-heading">
                    <h2>Tư vấn gần đây</h2>
                    <button className="text-link" onClick={() => go("history")}>
                      Tất cả <ArrowRight size={14} />
                    </button>
                  </div>
                  {data.messages.length ? (
                    <div className="recent-list">
                      {data.messages.slice(0, 2).map((entry) => (
                        <button
                          key={entry.id}
                          onClick={() => {
                            setActive(entry);
                            go("chat");
                          }}
                        >
                          <span className="mini-icon light-blue">
                            <MessageSquareText size={17} />
                          </span>
                          <div>
                            <strong>{entry.question}</strong>
                            <small>
                              Hồ sơ v{entry.revision} ·{" "}
                              {new Date(entry.createdAt).toLocaleTimeString(
                                "vi-VN",
                                {
                                  hour: "2-digit",
                                  minute: "2-digit",
                                  timeZone: "Asia/Ho_Chi_Minh",
                                },
                              )}
                            </small>
                          </div>
                          <ChevronRight size={16} />
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-inline">
                      <MessageSquareText size={28} />
                      <div>
                        <strong>Một câu hỏi, một bước rõ ràng hơn.</strong>
                        <p>Các cuộc tư vấn sẽ xuất hiện ở đây.</p>
                      </div>
                    </div>
                  )}
                </section>
              </div>
              <div className="page-footnote">
                <ShieldCheck size={15} /> CPA² sử dụng suy luận có kiểm chứng.
                Thông tin còn thiếu được thể hiện rõ trong từng câu trả lời.
              </div>
            </>
          )}

          {tab === "transcript" && (
            <>
              <PageHeading
                eyebrow="DỮ KIỆN CỦA BẠN"
                title="Hồ sơ & bảng điểm"
                description="Kiểm tra thông tin đầu vào để mỗi lời tư vấn có cơ sở chính xác."
              />
              <div className="transcript-top">
                <section className="panel">
                  <div className="panel-heading">
                    <h2>Thông tin sinh viên</h2>
                    <span className="subtle-tag">CNTT K49</span>
                  </div>
                  <div className="form-grid">
                    <label>
                      Mã hồ sơ
                      <input
                        value={draft.student_id}
                        maxLength={80}
                        onChange={(event) =>
                          updateDraft({
                            ...draft,
                            student_id: event.target.value,
                          })
                        }
                      />
                    </label>
                    <label>
                      Hồ sơ trải nghiệm
                      <select
                        aria-label="Chọn hồ sơ giả lập"
                        value=""
                        onChange={(event) => {
                          const value = data.demos.find(
                            (item) => item.id === event.target.value,
                          );
                          if (value) {
                            updateDraft(value.profile);
                            setOcrResult(null);
                          }
                        }}
                      >
                        <option value="">Chọn hồ sơ giả lập…</option>
                        {data.demos.map((item) => (
                          <option key={item.id} value={item.id}>
                            {item.name}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>
                  <div className="form-grid supplemental">
                    <label>
                      Thời gian đã học (năm)
                      <input
                        type="number"
                        min="0"
                        max="15"
                        step="0.5"
                        placeholder="Chưa khai báo"
                        value={
                          draft.da_hoc_nam2 == null
                            ? ""
                            : Number(draft.da_hoc_nam2) / 2
                        }
                        onChange={(event) =>
                          updateDraft({
                            ...draft,
                            da_hoc_nam2:
                              event.target.value === ""
                                ? null
                                : Number(event.target.value) * 2,
                          })
                        }
                      />
                    </label>
                    <label>
                      Tín chỉ được công nhận/chuyển đổi
                      <input
                        type="number"
                        min="0"
                        step="1"
                        placeholder="Chưa khai báo; nhập 0 nếu không có"
                        value={draft.tc_cong_nhan == null ? "" : Number(draft.tc_cong_nhan)}
                        onChange={(event) =>
                          updateDraft({
                            ...draft,
                            tc_cong_nhan: event.target.value === "" ? null : Number(event.target.value),
                          })
                        }
                      />
                    </label>
                    <label>
                      Xác nhận không bị kỷ luật
                      <select
                        value={
                          draft.xac_nhan_ky_luat_sach == null
                            ? ""
                            : String(draft.xac_nhan_ky_luat_sach)
                        }
                        onChange={(event) =>
                          updateDraft({
                            ...draft,
                            xac_nhan_ky_luat_sach:
                              event.target.value === ""
                                ? null
                                : event.target.value === "true",
                          })
                        }
                      >
                        <option value="">Chưa có thông tin</option>
                        <option value="true">Có xác nhận</option>
                        <option value="false">Không</option>
                      </select>
                    </label>
                    <label>
                      TC học phần từng bị F
                      <input
                        type="number"
                        min="0"
                        max="500"
                        placeholder="Chưa khai báo"
                        value={
                          draft.tc_diem_f == null ? "" : Number(draft.tc_diem_f)
                        }
                        onChange={(event) =>
                          updateDraft({
                            ...draft,
                            tc_diem_f:
                              event.target.value === ""
                                ? null
                                : Number(event.target.value),
                          })
                        }
                      />
                    </label>
                    <label>
                      Từng bị cảnh cáo cấp Trường
                      <select
                        value={
                          draft.ky_luat_canh_cao_cap_truong == null
                            ? ""
                            : String(draft.ky_luat_canh_cao_cap_truong)
                        }
                        onChange={(event) =>
                          updateDraft({
                            ...draft,
                            ky_luat_canh_cao_cap_truong:
                              event.target.value === ""
                                ? null
                                : event.target.value === "true",
                          })
                        }
                      >
                        <option value="">Chưa khai báo</option>
                        <option value="false">Không</option>
                        <option value="true">Có</option>
                      </select>
                    </label>
                  </div>
                </section>
                <section className="panel import-panel">
                  <div className="panel-heading">
                    <h2>Nhập bảng điểm</h2>
                    <Upload size={19} />
                  </div>
                  <p className="muted small">
                    Nhập hồ sơ CPA² hoặc bản xuất JSON từ niên luận AcademiQ.
                    Chỉ nhận CNTT K49.
                  </p>
                  <label className="upload-zone">
                    <FileJson size={28} />
                    <strong>Chọn file JSON</strong>
                    <span>Hồ sơ tối đa 1 MB</span>
                    <input
                      type="file"
                      accept=".json,application/json"
                      onChange={(event) => {
                        const file = event.target.files?.[0];
                        if (!file) return;
                        void run("import", async () => {
                          if (file.size > 1024 * 1024)
                            throw new Error("File JSON tối đa 1 MB.");
                          const value = JSON.parse(await file.text());
                          setRaw(pretty(value));
                          setNotice(
                            "Đã đọc JSON. Bấm Lưu hồ sơ để kiểm tra và chuyển đổi.",
                          );
                        });
                        event.target.value = "";
                      }}
                    />
                  </label>
                  <label className="consent">
                    <input
                      type="checkbox"
                      checked={consent}
                      onChange={(event) => setConsent(event.target.checked)}
                    />
                    Tôi đồng ý xử lý và lưu bảng điểm để nhận diện.
                  </label>
                  <label
                    className={`button outline full ${busy ? "disabled" : ""}`}
                  >
                    <Upload size={16} />
                    {busy === "ocr"
                      ? "Đang nhận diện…"
                      : "Nhận diện PDF / ảnh (OCR)"}
                    <input
                      type="file"
                      accept="application/pdf,image/png,image/jpeg"
                      multiple
                      disabled={!!busy}
                      hidden
                      onChange={(event) => {
                        const files = Array.from(event.target.files ?? []);
                        if (!files.length) return;
                        void run("ocr", async () => {
                          if (!consent)
                            throw new Error(
                              "Hãy tích đồng ý xử lý dữ liệu trước khi tải bảng điểm.",
                            );
                          if (
                            files.some((file) => file.size > 10 * 1024 * 1024)
                          )
                            throw new Error("Mỗi tệp tối đa 10 MB.");
                          if (
                            files.length > 4 ||
                            files.reduce((sum, file) => sum + file.size, 0) >
                              20 * 1024 * 1024
                          )
                            throw new Error(
                              "Tối đa 4 tệp, tổng dung lượng 20 MB và tổng 4 trang.",
                            );
                          const result = await ops.ocr(files, consent);
                          if (result) {
                            setOcrResult(result);
                            updateDraft(result.profile);
                            setReviewed(false);
                          } else
                            setNotice(
                              "Bảng điểm đang được xử lý. Kết quả sẽ tự xuất hiện khi hoàn tất.",
                            );
                        });
                        event.target.value = "";
                      }}
                    />
                  </label>
                  <small className="muted">
                    PDF/PNG/JPEG · tối đa 10 MB/tệp · tổng 20 MB ·{" "}
                    tổng 1–4 trang. Có thể tải bảng điểm trước khi lưu hồ sơ.
                  </small>
                </section>
              </div>
              {data.ocrStatus && (
                <div className="alert info" role="status">
                  <LoaderCircle
                    size={18}
                    className={
                      ["pending", "processing"].includes(data.ocrStatus)
                        ? "spin"
                        : ""
                    }
                  />
                  <span>
                    OCR:{" "}
                    {(
                      {
                        pending: "Đang chờ xử lý",
                        processing: "Đang nhận diện bảng điểm",
                        done: "Đã có bản nháp, cần rà soát",
                      } as Record<string, string>
                    )[data.ocrStatus] ?? data.ocrStatus}
                  </span>
                </div>
              )}
              {ocrResult && (
                <section className="panel ocr-review">
                  <h2>Bản nháp OCR — cần rà soát</h2>
                  <p>
                    Đã nhận diện {ocrResult.report.tong_dong ?? "—"} dòng học phần;
                    {" "}{Object.keys(ocrResult.profile.grades).length} môn đã qua
                    kiểm chéo. Các dòng chưa chắc cũng có trong danh sách, kèm
                    cảnh báo để đối chiếu.
                  </p>
                  {!!ocrResult.report.hoc_ky_lech?.length && (
                    <p>
                      Học kỳ cần đối chiếu: {ocrResult.report.hoc_ky_lech.join(", ")}.
                    </p>
                  )}
                  <p>
                    Hệ thống chưa dùng bản nháp này để kết luận. Dữ kiện chưa
                    chắc:{" "}
                    {ocrResult.report.khong_chac?.join(", ") ||
                      "xem báo cáo kiểm chéo"}
                    .
                  </p>
                  <details>
                    <summary>Xem báo cáo OCR</summary>
                    <pre>{pretty(ocrResult.report)}</pre>
                  </details>
                  <label className="checkbox">
                    <input
                      type="checkbox"
                      checked={reviewed}
                      onChange={(event) => setReviewed(event.target.checked)}
                    />{" "}
                    Tôi đã đối chiếu các dữ kiện được nhận với bảng điểm gốc.
                  </label>
                  <p className="muted small">
                    Nếu còn dòng thiếu hoặc chưa chắc, hãy nhập hồ sơ đầy đủ thủ
                    công. Xác nhận này không tự xác minh các dòng còn thiếu.
                  </p>
                </section>
              )}
              <section className="panel transcript-panel">
                <div className="panel-heading">
                  <h2>
                    Danh sách học phần{" "}
                    <span className="count">
                      {allTranscriptRows.length}
                    </span>
                  </h2>
                  <div className="search-field">
                    <Search size={16} />
                    <input
                      aria-label="Tìm học phần"
                      placeholder="Tìm mã hoặc tên học phần…"
                      value={filter}
                      onChange={(event) => setFilter(event.target.value)}
                    />
                  </div>
                </div>
                {reviewCount > 0 && (
                  <p className="ocr-list-warning" role="status">
                    <AlertTriangle size={17} aria-hidden="true" />
                    {reviewCount} dòng cần xem lại được tô vàng và xếp lên đầu.
                    Mở cảnh báo ở từng dòng để xem lý do và dữ liệu OCR gốc.
                    Điểm chưa chắc chưa được dùng để tư vấn.
                  </p>
                )}
                <div className="add-course">
                  <select
                    aria-label="Học phần cần thêm"
                    value={courseCode}
                    onChange={(event) => setCourseCode(event.target.value)}
                  >
                    <option value="">Chọn học phần cần thêm…</option>
                    {data.courses.map((course) => (
                      <option key={course.ma} value={course.ma}>
                        {course.ma} — {course.ten}
                      </option>
                    ))}
                  </select>
                  <input
                    aria-label="Điểm thang 10"
                    type="number"
                    min="0"
                    max="10"
                    step="0.1"
                    placeholder="Điểm 0–10"
                    value={score}
                    onChange={(event) => setScore(event.target.value)}
                  />
                  <button
                    className="button primary"
                    onClick={() => {
                      if (
                        !courseCode ||
                        score === "" ||
                        Number(score) < 0 ||
                        Number(score) > 10 ||
                        !Number.isFinite(Number(score))
                      ) {
                        setError("Chọn học phần và nhập điểm từ 0 đến 10.");
                        return;
                      }
                      const course = courseMap.get(courseCode)!;
                      const thang10 = Math.round(Number(score) * 10);
                      const grade = {
                        code: courseCode,
                        credits: course.tin_chi,
                        thang10,
                      };
                      updateDraft({
                        ...draft,
                        grades: {
                          ...draft.grades,
                          [courseCode]: {
                            ...grade,
                            letter: gradeLetter(grade),
                          },
                        },
                      });
                      setScore("");
                      setCourseCode("");
                    }}
                  >
                    <Plus size={16} /> Thêm
                  </button>
                </div>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Mã HP</th>
                        <th>Tên học phần</th>
                        <th>Tín chỉ</th>
                        <th>Điểm /10</th>
                        <th>Điểm chữ</th>
                        <th>
                          <span className="sr-only">Thao tác</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {shownGrades.map((row) => {
                        const { grade } = row;
                        const code = row.code ?? "";
                        return (
                        <tr key={row.key} className={row.needsReview ? "ocr-pending-row" : undefined}
                          data-review-status={row.needsReview ? "needs_review" : "accepted"}>
                          <td>
                            <strong>{code || "Chưa rõ mã"}</strong>
                          </td>
                          <td>
                            {courseMap.get(code)?.ten ?? "Chưa ánh xạ CTĐT"}
                            {row.needsReview && (
                              <details className="ocr-row-review">
                                <summary><AlertTriangle size={14} aria-hidden="true" /> Cần xem lại</summary>
                                {row.semester && <p>Học kỳ: {row.semester}</p>}
                                <ul>{row.reasons.map((reason, index) => <li key={index}>{reason}</li>)}</ul>
                                {row.raw && <pre>{row.raw}</pre>}
                                <p className="muted small">Giá trị OCR tạm thời; cần đối chiếu bảng điểm gốc.</p>
                              </details>
                            )}
                          </td>
                          <td>{grade.credits ?? "—"}</td>
                          <td>
                            {!row.stored ? (
                              <span aria-label={`Điểm OCR ${code || "chưa rõ mã"}`}>
                                {grade.thang10 == null ? "—" : grade.thang10 / 10}
                              </span>
                            ) : (
                            <input
                              aria-label={`Điểm ${code}`}
                              className="score-input"
                              type="number"
                              min="0"
                              max="10"
                              step="0.1"
                              value={
                                grade.thang10 == null ? "" : grade.thang10 / 10
                              }
                              placeholder="—"
                              onChange={(event) => {
                                const thang10 =
                                  event.target.value === ""
                                    ? null
                                    : Math.round(
                                        Number(event.target.value) * 10,
                                      );
                                const next = {
                                  ...grade,
                                  thang10,
                                  letter:
                                    thang10 == null
                                      ? undefined
                                      : gradeLetter({ code, thang10 }),
                                };
                                delete next.diem;
                                delete next.status;
                                updateDraft({
                                  ...draft,
                                  grades: { ...draft.grades, [code]: next },
                                });
                              }}
                            />
                            )}
                          </td>
                          <td>
                            <span
                              className={`grade-pill ${!row.needsReview && gradeLetter(grade) === "F" ? "fail" : ""}`}
                            >
                              {row.needsReview ? grade.letter ?? grade.diem ?? "—" : gradeLetter(grade)}
                            </span>
                          </td>
                          <td>
                            {row.stored && (
                            <button
                              className="icon-button danger-hover"
                              aria-label={`Xóa ${code}`}
                              onClick={() => {
                                const next = { ...draft.grades };
                                delete next[code];
                                updateDraft({ ...draft, grades: next });
                              }}
                            >
                              <Trash2 size={15} />
                            </button>
                            )}
                          </td>
                        </tr>
                        );
                      })}
                    </tbody>
                  </table>
                  {!shownGrades.length && (
                    <div className="empty-table">
                      Chưa có học phần phù hợp. Thêm học phần hoặc nhập bảng
                      điểm.
                    </div>
                  )}
                </div>
              </section>
              <details className="panel json-editor">
                <summary>
                  <FileJson size={17} /> Hồ sơ JSON và khai báo nâng cao{" "}
                  <ChevronDown size={17} />
                </summary>
                <p className="muted small">
                  Dùng để nhập chứng chỉ, quyết định miễn, lựa chọn tích lũy
                  hoặc chuyển đổi hồ sơ AcademiQ. Dữ liệu được kiểm tra khi lưu.
                </p>
                <textarea
                  aria-label="Hồ sơ JSON"
                  spellCheck={false}
                  value={raw}
                  onChange={(event) => setRaw(event.target.value)}
                  rows={16}
                />
              </details>
              <div className="save-bar">
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={consent}
                    onChange={(event) => setConsent(event.target.checked)}
                  />
                  <span>
                    {demo
                      ? "Tôi đồng ý xử lý hồ sơ trong phiên demo trên máy này."
                      : "Tôi đồng ý lưu hồ sơ và ảnh bảng điểm trên Convex, xử lý bằng dịch vụ CPA²."}
                  </span>
                </label>
                <div>
                  <button
                    className="button outline"
                    onClick={() =>
                      void run("export", async () =>
                        download("cpa2-profile.json", JSON.parse(raw)),
                      )
                    }
                  >
                    <ArrowDownToLine size={16} /> Xuất JSON
                  </button>
                  <button
                    className="button primary"
                    disabled={!!busy || !consent}
                    onClick={() => void save()}
                  >
                    {busy === "save" ? (
                      <LoaderCircle className="spin" size={16} />
                    ) : (
                      <Check size={16} />
                    )}{" "}
                    Lưu hồ sơ
                  </button>
                </div>
              </div>
            </>
          )}

          {tab === "chat" && (
            <>
              <div className="chat-heading">
                <div>
                  <span className="eyebrow">TƯ VẤN CÓ CHỨNG MINH</span>
                  <h1>Đi cùng bạn, từng quyết định.</h1>
                </div>
                <span className="subtle-tag">
                  <ShieldCheck size={13} /> Hồ sơ v{data.revision}
                </span>
              </div>
              <div className="chat-area">
                {!latest && (
                  <div className="chat-welcome">
                    <div className="chat-logo">
                      <Sparkles size={33} />
                    </div>
                    <h2>Hôm nay, bạn cần làm rõ điều gì?</h2>
                    <p>
                      Hỏi CPA² về điều kiện học tập của bạn.
                      <br />
                      Kết luận được suy ra từ dữ kiện và quy chế đã hình thức
                      hóa.
                    </p>
                    <div className="suggestion-grid">
                      {questions.map((text) => (
                        <button
                          key={text}
                          disabled={!!busy || !profile}
                          onClick={() => void send(text)}
                        >
                          {text}
                          <ArrowUpRight size={16} />
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {latest && (
                  <div className="conversation">
                    <div className="user-message">
                      <span className="message-avatar">SV</span>
                      <div>
                        <span className="message-author">
                          Bạn <small>· hồ sơ v{latest.revision}</small>
                        </span>
                        <p>{latest.question}</p>
                      </div>
                    </div>
                    <div className="assistant-message">
                      <span className="message-avatar assistant">
                        <Sparkles size={18} />
                      </span>
                      <div className="assistant-body">
                        <span className="message-author">
                          CPA²{" "}
                          <span className="verified-label">
                            <ShieldCheck size={12} /> Suy luận có kiểm chứng
                          </span>
                        </span>
                        <span
                          className={`verdict ${latest.result.verdict.toLowerCase()}`}
                        >
                          {labelVerdict[latest.result.verdict] ??
                            latest.result.verdict}
                        </span>
                        <p className="answer-text">
                          {latest.result.explanation_vi ??
                            "Xem chứng chỉ để kiểm tra kết quả."}
                        </p>
                        {Boolean(latest.result.missing_facts?.length) && (
                          <div className="missing-box">
                            <h4>
                              <CircleHelp size={16} /> Thông tin cần bổ sung
                            </h4>
                            <ul>
                              {latest.result.missing_facts?.map(
                                (fact, index) => (
                                  <li key={`${fact}-${index}`}>
                                    {latest.result.can_bo_sung?.find(
                                      (item) => item.bien === fact,
                                    )?.hoi ?? fact}
                                  </li>
                                ),
                              )}
                            </ul>
                            <button
                              className="text-link"
                              onClick={() => go("transcript")}
                            >
                              Cập nhật hồ sơ <ArrowRight size={14} />
                            </button>
                          </div>
                        )}
                        {Boolean(latest.result.mau_thuan?.length) && (
                          <div className="alert error">
                            {latest.result.mau_thuan?.join(" · ")}
                          </div>
                        )}
                        <button
                          className="proof-button"
                          onClick={() => setProof(latest.result)}
                        >
                          <ShieldCheck size={18} />
                          <span>
                            <strong>Xem chứng chỉ & nguồn quy chế</strong>
                            <small>
                              {latest.result.certificate?.proof?.steps
                                ?.length ?? 0}{" "}
                              bước chứng minh · KB{" "}
                              {latest.result.kb_version ?? "—"}
                            </small>
                          </span>
                          <ArrowUpRight size={17} />
                        </button>
                        {latest.result.de_xuat && (
                          <PlanResult plan={latest.result.de_xuat} />
                        )}
                      </div>
                    </div>
                  </div>
                )}
                {busy === "ask" && (
                  <div className="thinking" role="status">
                    <LoaderCircle size={17} className="spin" /> Đang kiểm tra dữ
                    kiện và chứng minh kết luận…
                  </div>
                )}
                <div ref={end} />
              </div>
              <form
                className="chat-composer"
                onSubmit={(event) => {
                  event.preventDefault();
                  void send(question);
                }}
              >
                <div>
                  <textarea
                    aria-label="Câu hỏi tư vấn"
                    placeholder={
                      profile
                        ? "Ví dụ: Em đủ điều kiện làm luận văn tốt nghiệp chưa?"
                        : "Hãy lưu hồ sơ trước khi đặt câu hỏi…"
                    }
                    value={question}
                    maxLength={2000}
                    onChange={(event) => setQuestion(event.target.value)}
                    onKeyDown={(event) => {
                      if (
                        event.key === "Enter" &&
                        !event.shiftKey &&
                        !event.nativeEvent.isComposing
                      ) {
                        event.preventDefault();
                        void send(question);
                      }
                    }}
                    disabled={!profile || !!busy}
                    rows={2}
                  />
                  <button
                    type="submit"
                    aria-label="Gửi câu hỏi"
                    disabled={!profile || !question.trim() || !!busy}
                  >
                    <Send size={19} />
                  </button>
                </div>
                <p>
                  <ShieldCheck size={12} /> CPA² trả lời trong phạm vi CTĐT CNTT
                  K49. Thiếu dữ kiện sẽ yêu cầu bổ sung.
                </p>
              </form>
            </>
          )}

          {tab === "plan" && (
            <>
              <PageHeading
                eyebrow="BƯỚC TIẾP THEO"
                title="Kế hoạch học tập"
                description="Chọn học phần cho một học kỳ, dựa trên những điều kiện đã chứng minh hợp lệ."
              />
              <section className="panel plan-controls">
                <div>
                  <label htmlFor="semester">Học kỳ dự kiến</label>
                  <select
                    id="semester"
                    value={semester}
                    onChange={(event) => {
                      setSemester(Number(event.target.value));
                      setPlan(null);
                    }}
                  >
                    <option value={1}>Học kỳ 1</option>
                    <option value={2}>Học kỳ 2</option>
                    <option value={3}>Học kỳ 3 (hè)</option>
                  </select>
                </div>
                <button
                  className="button primary"
                  disabled={!profile || !!busy}
                  onClick={() =>
                    void run("plan", async () =>
                      setPlan(await ops.recommend(semester)),
                    )
                  }
                >
                  {busy === "plan" ? (
                    <LoaderCircle className="spin" size={17} />
                  ) : (
                    <Sparkles size={17} />
                  )}{" "}
                  Tạo đề xuất học phần
                </button>
              </section>
              <div className="alert info">
                <ShieldCheck size={19} />
                <span>
                  Đề xuất xét tiên quyết, song hành, nhóm tự chọn và trần tín
                  chỉ. Ưu tiên chọn môn là chính sách tư vấn, cần đối chiếu lịch
                  mở lớp thực tế.
                </span>
              </div>
              {plan ? (
                <PlanResult plan={plan} />
              ) : (
                <Empty
                  icon={GraduationCap}
                  title="Một học kỳ có định hướng"
                  text="Chọn học kỳ và tạo đề xuất từ hồ sơ hiện tại của bạn."
                />
              )}
            </>
          )}

          {tab === "sources" && (
            <>
              <PageHeading
                eyebrow="CƠ SỞ CỦA MỌI KẾT LUẬN"
                title="Kho quy chế"
                description="Tra cứu các đoạn nguồn trong quy chế và chương trình đào tạo của CPA²."
              />
              <div className="source-cards">
                {[
                  {
                    title: "Quy chế đào tạo",
                    code: "QĐ 3266",
                    detail: "Tín chỉ, đăng ký học phần, đánh giá và tốt nghiệp",
                  },
                  {
                    title: "Miễn & công nhận học phần",
                    code: "QĐ 5339",
                    detail: "Chứng chỉ, xét miễn và chuyển đổi học phần",
                  },
                  {
                    title: "Chương trình đào tạo",
                    code: "CNTT K49",
                    detail: "Danh mục học phần, nhóm và điều kiện tiên quyết",
                  },
                ].map((source) => (
                  <div className="panel source-card" key={source.code}>
                    <BookOpen size={23} />
                    <span className="eyebrow">{source.code}</span>
                    <h3>{source.title}</h3>
                    <p>{source.detail}</p>
                  </div>
                ))}
              </div>
              <form
                className="source-search panel"
                onSubmit={(event) => {
                  event.preventDefault();
                  if (sourceQuestion.trim())
                    void run("lookup", async () => {
                      const result = await ops.lookup(sourceQuestion);
                      setPassages(result.passages);
                      setSearched(true);
                    });
                }}
              >
                <Search size={20} />
                <input
                  aria-label="Tìm trong quy chế"
                  placeholder="Nhập nội dung cần tra cứu, ví dụ: điểm W, điều kiện tốt nghiệp…"
                  value={sourceQuestion}
                  onChange={(event) => setSourceQuestion(event.target.value)}
                  maxLength={2000}
                />
                <button
                  className="button primary"
                  disabled={!!busy || !sourceQuestion.trim()}
                >
                  Tra cứu{" "}
                  {busy === "lookup" ? (
                    <LoaderCircle size={16} className="spin" />
                  ) : (
                    <ArrowRight size={16} />
                  )}
                </button>
              </form>
              <p className="muted small">
                Kết quả tra cứu là đoạn văn nguồn, không phải kết luận về hồ sơ
                sinh viên. Nguồn của câu trả lời cá nhân được lấy từ chứng chỉ.
              </p>
              {passages.map((passage, index) => (
                <article
                  className="panel passage"
                  key={String(passage.passage_id ?? index)}
                >
                  <span className="subtle-tag">
                    {String(passage.passage_id ?? "")}
                  </span>
                  <h3>
                    {String(passage.dia_chi ?? "Đoạn nguồn")}{" "}
                    {passage.trang != null && (
                      <small>· Trang {String(passage.trang)}</small>
                    )}
                  </h3>
                  <p>{String(passage.trich ?? "")}</p>
                </article>
              ))}
              {searched && !passages.length && (
                <Empty
                  icon={Search}
                  title="Chưa tìm thấy đoạn phù hợp"
                  text="Thử mô tả ngắn hơn hoặc dùng tên học phần, điều khoản."
                />
              )}
            </>
          )}

          {tab === "history" && (
            <>
              <PageHeading
                eyebrow="CÓ THỂ KIỂM TRA LẠI"
                title="Lịch sử tư vấn"
                description="Mỗi kết quả đi cùng phiên bản hồ sơ và nguồn tri thức đã sử dụng."
              />
              {!data.messages.length ? (
                <Empty
                  icon={History}
                  title="Chưa có cuộc tư vấn nào"
                  text="Đặt câu hỏi đầu tiên để bắt đầu lưu lại hành trình của bạn."
                />
              ) : (
                <div className="history-list">
                  {data.messages.map((entry) => (
                    <button
                      className="panel history-card"
                      key={entry.id}
                      onClick={() => {
                        setActive(entry);
                        go("chat");
                      }}
                    >
                      <span className="mini-icon light-blue">
                        <MessageSquareText size={21} />
                      </span>
                      <div>
                        <h3>{entry.question}</h3>
                        <p>
                          {new Date(entry.createdAt).toLocaleString("vi-VN", {
                            timeZone: "Asia/Ho_Chi_Minh",
                          })}{" "}
                          · Hồ sơ v{entry.revision} · KB{" "}
                          {entry.result.kb_version ?? "—"}
                        </p>
                      </div>
                      <span
                        className={`verdict ${entry.result.verdict.toLowerCase()}`}
                      >
                        {labelVerdict[entry.result.verdict] ??
                          entry.result.verdict}
                      </span>
                      <ChevronRight size={18} />
                    </button>
                  ))}
                </div>
              )}
            </>
          )}

          {tab === "settings" && (
            <>
              <PageHeading
                eyebrow="KHÔNG GIAN CỦA BẠN"
                title="Cài đặt & dữ liệu"
                description="Hiểu cách CPA² xử lý dữ liệu và chủ động quản lý thông tin của bạn."
              />
              <section className="panel settings-panel">
                <h2>
                  <ShieldCheck size={21} /> Dữ liệu và quyền riêng tư
                </h2>
                <p>
                  {demo
                    ? "Chế độ demo chạy trên máy cá nhân. Hồ sơ và lịch sử trong giao diện chỉ tồn tại trong bộ nhớ phiên; tải lại trang sẽ khôi phục hồ sơ mẫu. Ảnh OCR được xử lý trong thư mục tạm và xóa sau tác vụ."
                    : "Hồ sơ, ảnh OCR và lịch sử được lưu trên Convex dưới tài khoản Clerk của bạn. Dịch vụ Python chỉ nhận dữ liệu cần xử lý; không lưu bảng điểm vào log."}
                </p>
                <p>
                  Bản đầu dùng parser và lời giải theo mẫu. Chưa gửi hồ sơ đến
                  API mô hình AI bên ngoài.
                </p>
                <div className="settings-row">
                  <div>
                    <h3>Xuất hồ sơ hiện tại</h3>
                    <p>Tải bản JSON để kiểm tra hoặc nhập lại.</p>
                  </div>
                  <button
                    className="button outline"
                    disabled={!profile}
                    onClick={() => download("cpa2-profile.json", profile)}
                  >
                    <ArrowDownToLine size={16} /> Xuất dữ liệu
                  </button>
                </div>
                <div className="settings-row">
                  <div>
                    <h3>Xóa dữ liệu của tôi</h3>
                    <p>
                      Xóa hồ sơ, các phiên bản, hội thoại và ảnh đã đăng ký OCR.
                    </p>
                  </div>
                  <button
                    className="button danger"
                    onClick={() => setDeleteOpen(true)}
                  >
                    <Trash2 size={16} /> Xóa dữ liệu
                  </button>
                </div>
              </section>
              <section className="panel settings-panel">
                <h2>Về CPA²</h2>
                <p>
                  Certified Personalized Academic Advising — trợ lý tư vấn học
                  vụ có chứng minh, phát triển trong luận văn tốt nghiệp và kế
                  thừa các thành phần phù hợp từ niên luận AcademiQ.
                </p>
                <span className="subtle-tag">
                  Phạm vi demo: CNTT K49 · Đại học Cần Thơ
                </span>
              </section>
            </>
          )}
        </main>
      </div>
      {proof && <ProofDrawer result={proof} close={() => setProof(null)} />}
      {deleteOpen && (
        <div className="modal-backdrop">
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-title"
            className="confirm-dialog"
          >
            <Trash2 size={27} />
            <h2 id="delete-title">Xóa dữ liệu CPA²?</h2>
            <p>
              Thao tác này xóa hồ sơ, lịch sử và ảnh OCR đã đăng ký của tài
              khoản. Bạn có thể tạo lại hồ sơ mới sau đó.
            </p>
            <div>
              <button
                className="button outline"
                onClick={() => setDeleteOpen(false)}
              >
                Giữ dữ liệu
              </button>
              <button
                className="button danger"
                disabled={!!busy}
                onClick={() =>
                  void run("erase", async () => {
                    await ops.erase();
                    setActive(null);
                    setProof(null);
                    setPlan(null);
                    setOcrResult(null);
                    setDeleteOpen(false);
                    go("overview");
                    setNotice("Đã xóa dữ liệu CPA².");
                  })
                }
              >
                Xác nhận xóa
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

function PageHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>
          {title}
          <span className="heading-dot">.</span>
        </h1>
        <p>{description}</p>
      </div>
    </div>
  );
}
function Stat({
  label,
  value,
  suffix,
  icon: Icon,
  note,
  color,
}: {
  label: string;
  value: string;
  suffix: string;
  icon: typeof BookOpen;
  note: string;
  color: string;
}) {
  return (
    <section className="stat-card">
      <div className="stat-top">
        <span>{label}</span>
        <span className={`mini-icon ${color}`}>
          <Icon size={18} />
        </span>
      </div>
      <strong className="stat-value">
        {value}
        <small>{suffix}</small>
      </strong>
      <p>{note}</p>
    </section>
  );
}
function Empty({
  icon: Icon,
  title,
  text,
}: {
  icon: typeof BookOpen;
  title: string;
  text: string;
}) {
  return (
    <div className="empty-state">
      <span>
        <Icon size={31} />
      </span>
      <h2>{title}</h2>
      <p>{text}</p>
    </div>
  );
}
function PlanResult({ plan }: { plan: Recommendation }) {
  return (
    <section className="panel plan-result">
      <div className="panel-heading">
        <h2>Học phần đề xuất</h2>
        <span className="subtle-tag">{plan.tong_tc ?? 0} tín chỉ</span>
      </div>
      {plan.dang_ky?.length ? (
        <div className="plan-courses">
          {plan.dang_ky.map((course) => (
            <article key={course.ma}>
              <span className="course-code">{course.ma}</span>
              <div>
                <h3>{course.ten}</h3>
                <p>{course.ly_do}</p>
                <details>
                  <summary>Xem chứng chỉ điều kiện</summary>
                  <pre>{pretty(course.chung_chi)}</pre>
                </details>
              </div>
              <span>{course.tc} TC</span>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted">
          Chưa có học phần chắc chắn hợp lệ để đề xuất. Kiểm tra các thông tin
          cần xác minh dưới đây.
        </p>
      )}
      {Boolean(plan.can_xac_minh?.length) && (
        <div className="missing-box">
          <h4>Thông tin cần xác minh</h4>
          <ul>
            {plan.can_xac_minh?.map((item, index) => (
              <li key={index}>
                {item.ma && <strong>{item.ma}: </strong>}
                {item.ly_do}
              </li>
            ))}
          </ul>
        </div>
      )}
      <details className="result-json">
        <summary>Xem kết quả đầy đủ</summary>
        <pre>{pretty(plan)}</pre>
      </details>
    </section>
  );
}
function ProofDrawer({ result, close }: { result: Advice; close: () => void }) {
  const closeButton = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    closeButton.current?.focus();
    const handle = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    window.addEventListener("keydown", handle);
    return () => {
      window.removeEventListener("keydown", handle);
      previous?.focus();
    };
  }, [close]);
  return (
    <div className="drawer-backdrop" onClick={close}>
      <aside
        className="proof-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="proof-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="drawer-header">
          <span className="mini-icon green">
            <ShieldCheck size={22} />
          </span>
          <div>
            <span className="eyebrow">MINH BẠCH & KIỂM CHỨNG</span>
            <h2 id="proof-title">Chứng chỉ kết luận</h2>
          </div>
          <button
            ref={closeButton}
            className="icon-button"
            aria-label="Đóng chứng chỉ"
            onClick={close}
          >
            <X size={21} />
          </button>
        </div>
        <div className="drawer-body">
          <span className={`verdict ${result.verdict.toLowerCase()}`}>
            {labelVerdict[result.verdict] ?? result.verdict}
          </span>
          <p className="proof-claim">{result.claim ?? "Kết quả hậu kiểm"}</p>
          <h3>Các bước chứng minh</h3>
          {result.certificate?.proof?.steps?.length ? (
            result.certificate.proof.steps.map((step, index) => (
              <article className="proof-step" key={index}>
                <span className="step-number">{index + 1}</span>
                <div>
                  <code>{step.atom}</code>
                  <p>
                    {step.rule_id ?? "Quy tắc"} · {step.source?.van_ban}
                    {step.source?.dieu ? ` · Điều ${step.source.dieu}` : ""}
                    {step.source?.khoan ? ` khoản ${step.source.khoan}` : ""}
                  </p>
                  {step.source?.trich && (
                    <blockquote>{step.source.trich}</blockquote>
                  )}
                  {Boolean(step.facts?.length) && (
                    <details>
                      <summary>Dữ kiện sử dụng</summary>
                      <pre>{step.facts?.join("\n")}</pre>
                    </details>
                  )}
                </div>
              </article>
            ))
          ) : (
            <div className="inline-note">
              Chưa có chứng minh kết luận trong phạm vi câu hỏi hoặc dữ kiện
              hiện tại.
            </div>
          )}
          <h3>Nguồn gắn với chứng chỉ</h3>
          {result.nguon?.length ? (
            result.nguon.map((source, index) => (
              <div className="proof-source" key={index}>
                <strong>{source.dia_chi ?? source.passage_id}</strong>
                <small>
                  {source.trang != null
                    ? `Trang ${source.trang}`
                    : source.passage_id}
                </small>
                <p>{source.trich ?? String(source.text ?? "")}</p>
              </div>
            ))
          ) : (
            <p className="muted small">
              Không có đoạn nguồn được đính kèm cho kết quả này.
            </p>
          )}
          <button
            className="button outline full"
            onClick={() => download("cpa2-certificate.json", result)}
          >
            <ArrowDownToLine size={16} /> Tải kết quả & chứng chỉ JSON
          </button>
        </div>
      </aside>
    </div>
  );
}

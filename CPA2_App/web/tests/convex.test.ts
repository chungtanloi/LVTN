import { describe, expect, test, vi, afterEach } from "vitest";
import { defineTestApp } from "convex-test";
import schema from "../convex/schema";
import * as cpa2 from "../convex/cpa2";

const { api, internal, createTest } = defineTestApp({ schema }).defineModules({
  cpa2,
});
const profile = {
  student_id: "sv_test",
  major: "cntt",
  cohort: "K49",
  grades: {},
};
afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  vi.useRealTimers();
});

describe("CPA² data ownership and history", () => {
  test("saving cannot hide unresolved OCR rows by changing client metadata", async () => {
    const t = createTest();
    const id = await t.run((ctx) => ctx.db.insert("uploads", {
      owner: "alice", storageIds: [], status: "done", createdAt: Date.now(),
      result: { profile, report: { dong_can_ra_soat: [{ ma: "CT101" }] }, needs_review: true },
    }));
    const fetch = vi.fn(); vi.stubGlobal("fetch", fetch);
    await expect(t.withIdentity({ subject: "alice" }).action(api.cpa2.saveProfile, {
      consent: true, profile: { ...profile, meta: { nguon: "ocr", ocr_upload_id: id,
        reviewed_by_user: true, ocr_pending: false, ocr_report: {} } },
    })).rejects.toThrow("cảnh báo");
    expect(fetch).not.toHaveBeenCalled();
  });
  test("OCR review requires consent, isolates owners and prevents stale updates", async () => {
    const t = createTest();
    const original = { profile, report: { tai_lieu_ocr: { lich_su_ra_soat: [] } }, needs_review: true };
    const id = await t.run((ctx) => ctx.db.insert("uploads", {
      owner: "alice", storageIds: [], status: "done", result: original, createdAt: Date.now(),
    }));
    const alice = t.withIdentity({ subject: "alice" });
    const bob = t.withIdentity({ subject: "bob" });
    const fetch = vi.fn(); vi.stubGlobal("fetch", fetch);
    await expect(alice.action(api.cpa2.reviewOcr, { profile, change: {}, consent: false, uploadId: id }))
      .rejects.toThrow("đồng ý");
    await expect(bob.action(api.cpa2.reviewOcr, { profile, change: {}, consent: true, uploadId: id }))
      .rejects.toThrow("tài khoản");
    expect(fetch).not.toHaveBeenCalled();
    const result = { ...original, profile: { ...profile, meta: { ocr_upload_id: id } },
      report: { tai_lieu_ocr: { lich_su_ra_soat: [{ action: "approve" }] } } };
    await t.mutation(internal.cpa2.saveOcrReview, { id, owner: "alice", expected: 0, result });
    await expect(t.mutation(internal.cpa2.saveOcrReview, { id, owner: "alice", expected: 0, result }))
      .rejects.toThrow("thay đổi");
    const saved = await t.query(internal.cpa2.getUpload, { id });
    expect(saved!.result.profile.meta.ocr_review_updated_at).toBeTypeOf("number");
    await alice.mutation(api.cpa2.eraseData, {});
    await expect(t.mutation(internal.cpa2.saveOcrReview, { id, owner: "alice", expected: 1, result }))
      .rejects.toThrow("bị xóa");
  });
  test("new accounts can OCR their first PDF with consent and no saved profile", async () => {
    vi.useFakeTimers();
    vi.stubEnv("CPA2_API_URL", "https://python.test");
    vi.stubEnv("CPA2_SERVICE_KEY", "test-service-key");
    const t = createTest();
    const pdf = new Blob(["%PDF-test"], { type: "application/pdf" });
    const storageId = await t.run(async (ctx) => ctx.storage.store(pdf));
    const result = { profile, report: {}, needs_review: true };
    const fetch = vi.fn(async (url: string, init?: RequestInit) => {
      if (url === "https://python.test/v1/ocr") {
        const file = (init!.body as FormData).get("files") as File;
        expect(file.type).toBe("application/pdf");
        expect(file.name).toBe("page-0.pdf");
        expect(await file.text()).toBe("%PDF-test");
        return new Response(JSON.stringify(result), {
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(pdf);
    });
    vi.stubGlobal("fetch", fetch);
    const alice = t.withIdentity({ subject: "alice" });
    const id = await alice.mutation(api.cpa2.startOcr, {
      storageIds: [storageId],
      consent: true,
    });
    await t.finishAllScheduledFunctions(vi.runAllTimers);
    const upload = await t.query(internal.cpa2.getUpload, { id });
    expect(upload!.status).toBe("done");
    expect(upload!.result).toEqual({ ...result, profile: { ...profile, meta: { ocr_upload_id: id } } });
    expect(fetch).toHaveBeenCalledTimes(2);
    expect((await alice.query(api.cpa2.state, {})).profile).toBeNull();
  });

  test("OCR requires consent for a new account and respects explicit refusal", async () => {
    const t = createTest();
    const storageId = await t.run((ctx) => ctx.storage.store(
      new Blob(["%PDF-test"], { type: "application/pdf" }),
    ));
    const alice = t.withIdentity({ subject: "alice" });
    for (const consent of [undefined, false]) {
      await expect(alice.mutation(api.cpa2.startOcr, { storageIds: [storageId], consent }))
        .rejects.toThrow("đồng ý");
    }
    expect((await alice.query(api.cpa2.state, {})).uploads).toHaveLength(0);
    await t.mutation(internal.cpa2.persistProfile, { owner: "alice", profile });
    await expect(alice.mutation(api.cpa2.startOcr, { storageIds: [storageId], consent: false }))
      .rejects.toThrow("đồng ý");
  });


  test("unauthenticated reads and deletion are rejected", async () => {
    const t = createTest();
    await expect(t.query(api.cpa2.state, {})).rejects.toThrow("đăng nhập");
    await expect(t.mutation(api.cpa2.eraseData, {})).rejects.toThrow(
      "đăng nhập",
    );
  });

  test("another user cannot see or erase profiles and messages", async () => {
    const t = createTest();
    await t.mutation(internal.cpa2.persistProfile, { owner: "alice", profile });
    const snapshot = await t.query(internal.cpa2.latestSnapshot, {
      owner: "alice",
    });
    await t.mutation(internal.cpa2.recordMessage, {
      owner: "alice",
      snapshotId: snapshot!._id,
      question: "Tốt nghiệp?",
      result: { verdict: "UNKNOWN" },
    });
    const bob = t.withIdentity({ subject: "bob" });
    expect((await bob.query(api.cpa2.state, {})).profile).toBeNull();
    expect((await bob.query(api.cpa2.state, {})).messages).toHaveLength(0);
    await bob.mutation(api.cpa2.eraseData, {});
    const state = await t
      .withIdentity({ subject: "alice" })
      .query(api.cpa2.state, {});
    expect(state.profile).toEqual(profile);
    expect(state.messages).toHaveLength(1);
  });

  test("saving a new profile preserves earlier snapshot and message revisions", async () => {
    const t = createTest();
    await t.mutation(internal.cpa2.persistProfile, { owner: "alice", profile });
    const first = await t.query(internal.cpa2.latestSnapshot, {
      owner: "alice",
    });
    await t.mutation(internal.cpa2.recordMessage, {
      owner: "alice",
      snapshotId: first!._id,
      question: "Tốt nghiệp?",
      result: { verdict: "UNKNOWN" },
    });
    await t.mutation(internal.cpa2.persistProfile, {
      owner: "alice",
      profile: { ...profile, tc_diem_f: 0 },
    });
    const state = await t
      .withIdentity({ subject: "alice" })
      .query(api.cpa2.state, {});
    expect(state.revision).toBe(2);
    expect(state.messages[0].revision).toBe(1);
    expect(
      (await t.query(async (ctx) => await ctx.db.get(first!._id)))?.profile,
    ).toEqual(profile);
  });

  test("deletion prevents an in-flight answer from recreating history", async () => {
    const t = createTest();
    await t.mutation(internal.cpa2.persistProfile, { owner: "alice", profile });
    const first = await t.query(internal.cpa2.latestSnapshot, {
      owner: "alice",
    });
    const alice = t.withIdentity({ subject: "alice" });
    await alice.mutation(api.cpa2.eraseData, {});
    await expect(
      t.mutation(internal.cpa2.recordMessage, {
        owner: "alice",
        snapshotId: first!._id,
        question: "Late result",
        result: {},
      }),
    ).rejects.toThrow("bị xóa");
    expect((await alice.query(api.cpa2.state, {})).messages).toHaveLength(0);
  });

  test("profile upload requires explicit consent before contacting Python", async () => {
    const t = createTest().withIdentity({ subject: "alice" });
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    await expect(
      t.action(api.cpa2.saveProfile, { profile, consent: false }),
    ).rejects.toThrow("đồng ý");
    expect(fetch).not.toHaveBeenCalled();
  });

  test("a profile save already in flight cannot recreate erased data", async () => {
    const t = createTest();
    const quotaId = await t.mutation(internal.cpa2.takeQuota, {
      owner: "alice",
    });
    await t.withIdentity({ subject: "alice" }).mutation(api.cpa2.eraseData, {});
    await expect(
      t.mutation(internal.cpa2.persistProfile, {
        owner: "alice",
        profile,
        quotaId,
      }),
    ).rejects.toThrow("bị xóa");
  });

  test("PDF uploads reject unsupported MIME types and accept standalone PDFs", async () => {
    const t = createTest();
    await t.mutation(internal.cpa2.persistProfile, { owner: "alice", profile });
    const [pdf, png, other] = await t.run(async (ctx) => [
      await ctx.storage.store(
        new Blob(["%PDF-1.7"], { type: "application/pdf" }),
      ),
      await ctx.storage.store(new Blob(["png"], { type: "image/png" })),
      await ctx.storage.store(new Blob(["x"], { type: "text/plain" })),
    ]);
    const alice = t.withIdentity({ subject: "alice" });
    await expect(
      alice.mutation(api.cpa2.startOcr, { storageIds: [other] }),
    ).rejects.toThrow("PDF");
    await expect(
      alice.mutation(api.cpa2.startOcr, { storageIds: [pdf] }),
    ).resolves.toBeTruthy();
  });

  test("per-user request limits are enforced independently", async () => {
    const t = createTest();
    for (let index = 0; index < 10; index++)
      await t.mutation(internal.cpa2.takeQuota, { owner: "alice" });
    await expect(
      t.mutation(internal.cpa2.takeQuota, { owner: "alice" }),
    ).rejects.toThrow("nhiều yêu cầu");
    await expect(
      t.mutation(internal.cpa2.takeQuota, { owner: "bob" }),
    ).resolves.not.toThrow();
  });
});

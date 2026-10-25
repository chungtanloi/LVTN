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
afterEach(() => vi.unstubAllGlobals());

describe("CPA² data ownership and history", () => {
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

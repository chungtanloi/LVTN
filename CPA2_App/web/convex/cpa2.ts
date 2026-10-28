import { anyApi } from "convex/server";
import {
  action,
  query,
  mutation,
  internalMutation,
  internalQuery,
  internalAction,
} from "./bindings";
import { ConvexError, v } from "convex/values";

async function user(ctx: {
  auth: { getUserIdentity: () => Promise<{ subject: string } | null> };
}) {
  const identity = await ctx.auth.getUserIdentity();
  if (!identity) throw new ConvexError("Bạn cần đăng nhập để tiếp tục.");
  return identity.subject;
}
async function python(path: string, body?: unknown, timeout = 35000) {
  const url = process.env.CPA2_API_URL,
    key = process.env.CPA2_SERVICE_KEY;
  if (!url || !key) throw new ConvexError("Dịch vụ tư vấn chưa được cấu hình.");
  const response = await fetch(`${url.replace(/\/$/, "")}${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      Authorization: `Bearer ${key}`,
      ...(body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
    },
    body:
      body === undefined
        ? undefined
        : body instanceof FormData
          ? body
          : JSON.stringify(body),
    signal: AbortSignal.timeout(timeout),
  });
  const result = await response.json();
  if (!response.ok)
    throw new ConvexError(
      typeof result.detail === "string"
        ? result.detail
        : "Dữ liệu không hợp lệ.",
    );
  return result;
}

export const state = query({
  args: {},
  handler: async (ctx) => {
    const owner = await user(ctx);
    const profile = await ctx.db
      .query("profiles")
      .withIndex("by_owner", (q) => q.eq("owner", owner))
      .unique();
    const messages = await ctx.db
      .query("messages")
      .withIndex("by_owner", (q) => q.eq("owner", owner))
      .order("desc")
      .take(100);
    const uploads = await ctx.db
      .query("uploads")
      .withIndex("by_owner", (q) => q.eq("owner", owner))
      .order("desc")
      .take(10);
    return {
      profile: profile?.profile ?? null,
      revision: profile?.revision ?? 0,
      messages: messages.map((m) => ({
        id: m._id,
        question: m.question,
        result: m.result,
        createdAt: m.createdAt,
        revision: m.revision,
      })),
      uploads,
    };
  },
});
export const configuration = action({
  args: {},
  handler: async (ctx) => {
    await user(ctx);
    return {
      catalog: await python("/v1/catalog"),
      demos: await python("/v1/demo-profiles"),
    };
  },
});
export const takeQuota = internalMutation({
  args: { owner: v.string() },
  handler: async (ctx, { owner }) => {
    const now = Date.now();
    const entry = await ctx.db
      .query("limits")
      .withIndex("by_owner", (q) => q.eq("owner", owner))
      .unique();
    if (entry && now - entry.startedAt < 60000) {
      if (entry.count >= 10)
        throw new ConvexError(
          "Bạn đã gửi nhiều yêu cầu. Hãy thử lại sau một phút.",
        );
      await ctx.db.patch(entry._id, { count: entry.count + 1 });
    } else if (entry)
      await ctx.db.patch(entry._id, { count: 1, startedAt: now });
    else
      return await ctx.db.insert("limits", { owner, count: 1, startedAt: now });
    return entry._id;
  },
});
export const persistProfile = internalMutation({
  args: {
    owner: v.string(),
    profile: v.any(),
    quotaId: v.optional(v.id("limits")),
  },
  handler: async (ctx, { owner, profile, quotaId }) => {
    if (quotaId && (await ctx.db.get(quotaId))?.owner !== owner)
      throw new ConvexError(
        "Dữ liệu đã bị xóa. Hãy lưu lại nếu bạn muốn tạo hồ sơ mới.",
      );
    const existing = await ctx.db
      .query("profiles")
      .withIndex("by_owner", (q) => q.eq("owner", owner))
      .unique();
    const now = Date.now(),
      revision = (existing?.revision ?? 0) + 1;
    if (existing)
      await ctx.db.patch(existing._id, { profile, revision, updatedAt: now });
    else
      await ctx.db.insert("profiles", {
        owner,
        profile,
        revision,
        consentedAt: now,
        updatedAt: now,
      });
    await ctx.db.insert("snapshots", {
      owner,
      profile,
      revision,
      createdAt: now,
    });
    return { profile, revision };
  },
});
export const saveProfile = action({
  args: { profile: v.any(), consent: v.boolean() },
  handler: async (ctx, args) => {
    const owner = await user(ctx);
    if (!args.consent) throw new ConvexError("Cần đồng ý trước khi lưu hồ sơ.");
    const quotaId = await ctx.runMutation(anyApi.cpa2.takeQuota, { owner });
    const validated = await python("/v1/profiles/validate", {
      profile: args.profile,
    });
    return await ctx.runMutation(anyApi.cpa2.persistProfile, {
      owner,
      profile: validated.profile,
      quotaId,
    });
  },
});
export const latestSnapshot = internalQuery({
  args: { owner: v.string() },
  handler: async (ctx, { owner }) =>
    await ctx.db
      .query("snapshots")
      .withIndex("by_owner", (q) => q.eq("owner", owner))
      .order("desc")
      .first(),
});
export const recordMessage = internalMutation({
  args: {
    owner: v.string(),
    snapshotId: v.id("snapshots"),
    question: v.string(),
    result: v.any(),
  },
  handler: async (ctx, args) => {
    const snapshot = await ctx.db.get(args.snapshotId);
    // A concurrent delete must not recreate the deleted user's history.
    if (!snapshot || snapshot.owner !== args.owner)
      throw new ConvexError("Hồ sơ đã thay đổi hoặc bị xóa.");
    const createdAt = Date.now();
    const id = await ctx.db.insert("messages", {
      ...args,
      revision: snapshot.revision,
      createdAt,
    });
    return {
      id,
      question: args.question,
      result: args.result,
      revision: snapshot.revision,
      createdAt,
    };
  },
});
export const advise = action({
  args: { question: v.string() },
  handler: async (ctx, { question }) => {
    const owner = await user(ctx);
    if (!question.trim() || question.length > 2000)
      throw new ConvexError("Câu hỏi cần có từ 1 đến 2.000 ký tự.");
    await ctx.runMutation(anyApi.cpa2.takeQuota, { owner });
    const snapshot = await ctx.runQuery(anyApi.cpa2.latestSnapshot, { owner });
    if (!snapshot) throw new ConvexError("Hãy lưu hồ sơ trước khi tư vấn.");
    const result = await python("/v1/advice", {
      question,
      profile: snapshot.profile,
    });
    return await ctx.runMutation(anyApi.cpa2.recordMessage, {
      owner,
      snapshotId: snapshot._id,
      question,
      result,
    });
  },
});
export const lookup = action({
  args: { question: v.string() },
  handler: async (ctx, args) => {
    const owner = await user(ctx);
    await ctx.runMutation(anyApi.cpa2.takeQuota, { owner });
    return await python("/v1/lookup", args);
  },
});
export const recommend = action({
  args: { semester: v.number() },
  handler: async (ctx, { semester }) => {
    const owner = await user(ctx);
    await ctx.runMutation(anyApi.cpa2.takeQuota, { owner });
    if (![1, 2, 3].includes(semester))
      throw new ConvexError("Học kỳ phải là 1, 2 hoặc 3.");
    const snapshot = await ctx.runQuery(anyApi.cpa2.latestSnapshot, { owner });
    if (!snapshot) throw new ConvexError("Hãy lưu hồ sơ trước.");
    return await python("/v1/recommendations", {
      profile: snapshot.profile,
      semester,
    });
  },
});
export const uploadUrl = mutation({
  args: { consent: v.boolean() },
  handler: async (ctx, { consent }) => {
    await user(ctx);
    if (!consent)
      throw new ConvexError("Cần đồng ý xử lý và lưu ảnh bảng điểm.");
    return await ctx.storage.generateUploadUrl();
  },
});
export const startOcr = mutation({
  args: {
    storageIds: v.array(v.id("_storage")),
    consent: v.optional(v.boolean()),
  },
  handler: async (ctx, { storageIds, consent }) => {
    const owner = await user(ctx);
    const profile = await ctx.db
      .query("profiles")
      .withIndex("by_owner", (q) => q.eq("owner", owner))
      .unique();
    // Existing clients may rely on consent recorded with their saved profile.
    // New accounts can import their first transcript without creating a profile.
    if (consent === false || (!profile && consent !== true))
      throw new ConvexError(
        "Cần đồng ý xử lý và lưu bảng điểm trước khi OCR.",
      );
    if (
      storageIds.length < 1 ||
      storageIds.length > 4 ||
      new Set(storageIds).size !== storageIds.length
    )
      throw new ConvexError("Chọn PDF hoặc ảnh khác nhau, tổng tối đa 4 trang.");
    let size = 0;
    for (const storageId of storageIds) {
      const file = await ctx.db.system.get(storageId);
      if (
        !file ||
        file.size > 10 * 1024 * 1024 ||
        !["image/png", "image/jpeg", "application/pdf"].includes(file.contentType ?? "")
      )
        throw new ConvexError("Chỉ nhận PDF hoặc ảnh PNG/JPEG tối đa 10 MB/tệp.");
      size += file.size;
      const existing = await ctx.db
        .query("files")
        .withIndex("by_storage", (q) => q.eq("storageId", storageId))
        .first();
      if (existing) throw new ConvexError("Ảnh đã được đăng ký xử lý.");
      await ctx.db.insert("files", { owner, storageId });
    }
    if (size > 20 * 1024 * 1024)
      throw new ConvexError("Tổng dung lượng tệp tối đa 20 MB.");
    const recent = await ctx.db
      .query("uploads")
      .withIndex("by_owner", (q) => q.eq("owner", owner))
      .order("desc")
      .take(10);
    if (recent.filter((x) => Date.now() - x.createdAt < 60000).length >= 3)
      throw new ConvexError("Tối đa 3 tác vụ OCR mỗi phút.");
    const id = await ctx.db.insert("uploads", {
      owner,
      storageIds,
      status: "pending",
      createdAt: Date.now(),
    });
    await ctx.scheduler.runAfter(0, anyApi.cpa2.processOcr, { id });
    return id;
  },
});
export const getUpload = internalQuery({
  args: { id: v.id("uploads") },
  handler: async (ctx, { id }) => {
    const upload = await ctx.db.get(id);
    return upload
      ? {
          ...upload,
          urls: await Promise.all(
            upload.storageIds.map((id) => ctx.storage.getUrl(id)),
          ),
        }
      : null;
  },
});
export const finishOcr = internalMutation({
  args: {
    id: v.id("uploads"),
    status: v.union(
      v.literal("processing"),
      v.literal("done"),
      v.literal("error"),
    ),
    result: v.optional(v.any()),
    error: v.optional(v.string()),
  },
  handler: async (ctx, { id, ...patch }) => {
    if (await ctx.db.get(id)) await ctx.db.patch(id, patch);
  },
});
export const processOcr = internalAction({
  args: { id: v.id("uploads") },
  handler: async (ctx, { id }) => {
    const upload = await ctx.runQuery(anyApi.cpa2.getUpload, { id });
    if (!upload?.urls?.length) return;
    await ctx.runMutation(anyApi.cpa2.finishOcr, { id, status: "processing" });
    try {
      const form = new FormData();
      for (const [index, url] of upload.urls.entries()) {
        if (!url) throw new Error("Không tìm thấy ảnh.");
        const file = await fetch(url, { signal: AbortSignal.timeout(15000) });
        if (!file.ok) throw new Error("Không đọc được ảnh.");
        const blob = await file.blob();
        const extension = blob.type === "application/pdf" ? "pdf" : "png";
        form.append("files", blob, `page-${index}.${extension}`);
      }
      const result = await python("/v1/ocr", form, 250000);
      await ctx.runMutation(anyApi.cpa2.finishOcr, {
        id,
        status: "done",
        result,
      });
    } catch {
      await ctx.runMutation(anyApi.cpa2.finishOcr, {
        id,
        status: "error",
        error: "OCR chưa thành công. Kiểm tra tệp PDF/ảnh (tổng tối đa 4 trang), thử ảnh rõ hơn hoặc nhập JSON.",
      });
    }
  },
});
export const eraseData = mutation({
  args: {},
  handler: async (ctx) => {
    const owner = await user(ctx);
    for (const name of [
      "profiles",
      "snapshots",
      "messages",
      "uploads",
      "files",
      "limits",
    ] as const) {
      const rows = await ctx.db
        .query(name)
        .withIndex("by_owner", (q) => q.eq("owner", owner))
        .collect();
      for (const row of rows) {
        if ("storageId" in row) await ctx.storage.delete(row.storageId);
        await ctx.db.delete(row._id);
      }
    }
  },
});

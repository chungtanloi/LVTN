import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  profiles: defineTable({
    owner: v.string(),
    profile: v.any(),
    revision: v.number(),
    consentedAt: v.number(),
    updatedAt: v.number(),
  }).index("by_owner", ["owner"]),
  snapshots: defineTable({
    owner: v.string(),
    revision: v.number(),
    profile: v.any(),
    createdAt: v.number(),
  }).index("by_owner", ["owner"]),
  messages: defineTable({
    owner: v.string(),
    snapshotId: v.id("snapshots"),
    revision: v.number(),
    question: v.string(),
    result: v.any(),
    createdAt: v.number(),
  }).index("by_owner", ["owner"]),
  uploads: defineTable({
    owner: v.string(),
    storageIds: v.array(v.id("_storage")),
    status: v.union(
      v.literal("pending"),
      v.literal("processing"),
      v.literal("done"),
      v.literal("error"),
    ),
    result: v.optional(v.any()),
    error: v.optional(v.string()),
    createdAt: v.number(),
  }).index("by_owner", ["owner"]),
  files: defineTable({ owner: v.string(), storageId: v.id("_storage") })
    .index("by_owner", ["owner"])
    .index("by_storage", ["storageId"]),
  limits: defineTable({
    owner: v.string(),
    startedAt: v.number(),
    count: v.number(),
  }).index("by_owner", ["owner"]),
});

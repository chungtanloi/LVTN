import { NextRequest, NextResponse } from "next/server";
import { pythonRequest } from "@/lib/service";

export const runtime = "nodejs";
export const maxDuration = 150;
const paths: Record<string, string> = {
  catalog: "/v1/catalog",
  profiles: "/v1/demo-profiles",
  validate: "/v1/profiles/validate",
  advice: "/v1/advice",
  lookup: "/v1/lookup",
  recommendations: "/v1/recommendations",
  ocr: "/v1/ocr",
};
const visits = new Map<string, { count: number; until: number }>();

async function handle(
  request: NextRequest,
  context: { params: Promise<{ operation: string }> },
) {
  // This bypass is for loopback development only, never an alternative to Clerk in production.
  if (
    process.env.CPA2_DEMO_MODE !== "true" ||
    process.env.NODE_ENV === "production" ||
    !["localhost", "127.0.0.1", "[::1]"].includes(request.nextUrl.hostname)
  ) {
    return NextResponse.json(
      { error: "Chế độ demo cục bộ chưa được bật." },
      { status: 403 },
    );
  }
  const origin = request.headers.get("origin");
  let sameOrigin = false;
  try {
    sameOrigin = Boolean(
      origin &&
      new URL(origin).host === request.headers.get("host") &&
      new URL(origin).protocol === "http:",
    );
  } catch {
    /* Invalid origins are rejected. */
  }
  if (request.method === "POST" && !sameOrigin)
    return NextResponse.json(
      { error: "Nguồn yêu cầu không hợp lệ." },
      { status: 403 },
    );
  const operation = (await context.params).operation;
  if (
    !paths[operation] ||
    (request.method === "GET") !== ["catalog", "profiles"].includes(operation)
  )
    return NextResponse.json(
      { error: "Không tìm thấy tác vụ." },
      { status: 404 },
    );
  const now = Date.now();
  for (const [key, entry] of visits) if (entry.until < now) visits.delete(key);
  const entry = visits.get("local") ?? { count: 0, until: now + 60000 };
  if (++entry.count > 40)
    return NextResponse.json(
      { error: "Có quá nhiều yêu cầu. Vui lòng thử lại sau một phút." },
      { status: 429 },
    );
  visits.set("local", entry);
  if (Number(request.headers.get("content-length") ?? 0) > 21 * 1024 * 1024)
    return NextResponse.json({ error: "Tệp quá lớn." }, { status: 413 });
  try {
    const body =
      request.method === "GET"
        ? undefined
        : operation === "ocr"
          ? await request.formData()
          : await request.json();
    return NextResponse.json(
      await pythonRequest(
        paths[operation],
        body,
        operation === "ocr" ? 250000 : 35000,
      ),
    );
  } catch (error) {
    return NextResponse.json(
      {
        error:
          error instanceof Error
            ? error.message
            : "Không kết nối được dịch vụ CPA².",
      },
      { status: 502 },
    );
  }
}
export const GET = handle;
export const POST = handle;

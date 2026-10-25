import "server-only";

export async function pythonRequest(
  path: string,
  body?: unknown,
  timeout = 35000,
) {
  const url = process.env.CPA2_API_URL;
  const key = process.env.CPA2_SERVICE_KEY;
  if (!url || !key)
    throw new Error(
      "Chưa cấu hình CPA2_API_URL và CPA2_SERVICE_KEY cho dịch vụ Python.",
    );
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
    cache: "no-store",
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Dữ liệu gửi lên không hợp lệ.",
    );
  return data;
}

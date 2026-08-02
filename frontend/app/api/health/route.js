// Direct health-check endpoint — responds immediately without proxying to the backend.
// Used by Railway's healthcheck to confirm the frontend is alive.
export async function GET() {
  return Response.json({ status: "ok", service: "frontend" });
}

export async function GET(req) {
  const { searchParams } = new URL(req.url);
  const pathname = searchParams.get("pathname");

  if (!pathname) {
    return new Response(JSON.stringify({ error: "Missing pathname parameter" }), { status: 400 });
  }

  const apiUrl = `http://localhost:8000/api${pathname}`;

  try {
    const backendResponse = await fetch(apiUrl, { method: "GET" });
    const data = await backendResponse.json();
    return new Response(JSON.stringify(data), { status: backendResponse.status });
  } catch (error) {
    console.error("Proxy error:", error);
    return new Response(JSON.stringify({ error: "Internal Server Error" }), { status: 500 });
  }
}

export async function POST(req) {
  const { pathname, body } = await req.json();

  if (!pathname) {
    return new Response(JSON.stringify({ error: "Missing pathname parameter" }), { status: 400 });
  }

  const apiUrl = `http://localhost:8000/api${pathname}`;

  try {
    const backendResponse = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await backendResponse.json();
    return new Response(JSON.stringify(data), { status: backendResponse.status });
  } catch (error) {
    console.error("Proxy error:", error);
    return new Response(JSON.stringify({ error: "Internal Server Error" }), { status: 500 });
  }
}

export async function DELETE(req) {
  const { pathname } = await req.json();

  if (!pathname) {
    return new Response(JSON.stringify({ error: "Missing pathname parameter" }), { status: 400 });
  }

  const apiUrl = `http://localhost:8000/api${pathname}`;

  try {
    const backendResponse = await fetch(apiUrl, { method: "DELETE" });
    const data = await backendResponse.json();
    return new Response(JSON.stringify(data), { status: backendResponse.status });
  } catch (error) {
    console.error("Proxy error:", error);
    return new Response(JSON.stringify({ error: "Internal Server Error" }), { status: 500 });
  }
}
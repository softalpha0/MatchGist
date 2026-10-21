import type { Fan, MatchInfo } from "./types";

// Same origin in production (FastAPI serves this site). For `npm run dev`, point at the API:
//   $env:NEXT_PUBLIC_API_BASE = "http://127.0.0.1:8000"
export const API = process.env.NEXT_PUBLIC_API_BASE ?? "";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

export async function getConfig(): Promise<{ model: string; llm_mode: string; speech: boolean; storylines: string[] }> {
  return json(await fetch(`${API}/config`));
}

export async function listMatches(): Promise<MatchInfo[]> {
  return json(await fetch(`${API}/matches`));
}

/** A fresh live run of a pre-generated demo match, at the chosen speed. */
export async function startReplay(storyline: string, speed: number): Promise<MatchInfo> {
  return json(
    await fetch(`${API}/matches/demo-${storyline}/replay`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ speed }),
    }),
  );
}

export async function addFan(matchId: string, fan: Fan): Promise<unknown> {
  return json(
    await fetch(`${API}/matches/${matchId}/fans`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(fan),
    }),
  );
}

export function streamUrl(matchId: string): string {
  return `${API}/matches/${matchId}/stream`;
}

export function audioUrl(path: string): string {
  return `${API}${path}`;
}

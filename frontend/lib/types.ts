// Shapes of what the MatchGist backend streams (see backend/app: schema, ledger, moments).

export type Channel = "broadcast" | "sms" | "chat" | "voice" | "watch" | "push";
export type Language = "en" | "hi" | "id" | "pt-BR" | "ar" | "pcm";

export interface Fan {
  fan_id: string;
  display_name: string;
  language: Language;
  mode: "analyst" | "casual" | "club_focus" | "player_focus" | "single_metric";
  favorite_club: string | null;
  favorite_player: string | null;
  focus_metric: string | null;
  channel: Channel;
  data_budget_kb: number | null;
  max_pings: number | null;
  only_if_involved: boolean;
  quiet_after_minute: number | null;
}

export interface Budget {
  data_kb_left: number | null;
  pings_left: number | null;
  data_used_kb: number;
  pings_used: number;
  binding: "pings" | "data" | "none";
}

export interface LedgerSummary extends Budget {
  fan_id: string;
  channel: Channel;
  deliveries: number;
  skipped: number;
  data_budget_kb: number | null;
  max_pings: number | null;
}

export interface OverlayCue {
  cue_id: string;
  match_clock: string;
  period: number;
  show_at_ms: number;
  duration_ms: number;
  slot: "lower_third" | "top_bar" | "side_panel" | "player_tag";
  template: string;
  anchor_player_id: string | null;
  data: Record<string, unknown>;
  text: string;
}

export interface Delivery {
  delivery_id: string;
  fan_id: string;
  kind: "moment" | "bundle" | "digest" | "overlay";
  moment_ids: string[];
  channel: Channel;
  language: Language;
  match_clock: string;
  text: string;
  title: string | null;
  value: string | null;
  audio_url: string | null;
  audio_seconds: number | null;
  voice: string | null;
  size_kb: number;
  segments: number | null;
  encoding: string | null;
  budget_after: Budget;
  decision_reason: string;
  fallback_used: boolean;
  attempts: number;
  overlay: OverlayCue | null;
}

export interface AgentEvent {
  ts: number;
  match_clock: string;
  agent: string;
  action: string;
  detail: string;
  fan_id: string | null;
  moment_id: string | null;
  latency_ms: number | null;
  model: string | null;
}

export interface Moment {
  moment_id: string;
  type: string;
  match_clock: string;
  period: number;
  minute: number;
  team_id: string | null;
  player_id: string | null;
  base_score: number;
  facts: Record<string, unknown>;
  event_id?: string | null;
  source_event_ids?: string[];
}

export interface TeamSnap {
  club_id: string;
  name: string;
  goals: number;
  possession: number | null;
  passes: number;
  pass_accuracy: number | null;
  shots: number;
  shots_on_target: number;
  xg: number;
  pressure_index: number | null;
  players_on_pitch: number;
}

export interface Snapshot {
  match_id: string;
  match_clock: string;
  minute: number;
  period: number;
  status: string;
  score: [number, number];
  possession: string | null;
  momentum: number;
  home: TeamSnap;
  away: TeamSnap;
  speed?: number;
  storyline?: string;
  model?: string;
  fans?: Fan[];
  ledgers?: Record<string, LedgerSummary>;
}

export interface MatchEvent {
  event_id: string;
  seq: number;
  match_clock: string;
  period: number;
  type: string;
  team_id?: string;
  player_id?: string;
  x?: number;
  y?: number;
  end_x?: number;
  end_y?: number;
  outcome?: string;
  speed_kmh?: number; // ball speed (passes, shots), carry speed
  top_speed_kmh?: number; // sprint
  distance_m?: number;
  total_km?: number; // distance milestone
}

export interface MatchInfo {
  match_id: string;
  storyline: string;
  speed: number;
  home: string;
  away: string;
  status: string;
}

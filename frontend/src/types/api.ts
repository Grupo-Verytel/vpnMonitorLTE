export type ChannelType = 'LTE' | 'FIBRA' | 'DOWN' | 'UNKNOWN';

export interface SitesSummary {
  evaluated_at: string;
  total_sites: number;
  sites_lte: number;
  sites_fibra: number;
  sites_down: number;
  pct_lte: number;
  pct_fibra: number;
  pct_down: number;
  last_snapshot_time: string | null;
}

export interface SiteListItem {
  tunnel_name: string;
  site_name: string | null;
  site_address: string | null;
  locality: string | null;
  project_code: string | null;
  channel: ChannelType;
  current_status: string;
  traffic_bytes_per_min: number;
  traffic_last_5m_bytes: number;
  last_lte_at: string | null;
  lte_minutes_today: number;
  remote_gateway: string | null;
}

export interface SiteListResponse {
  items: SiteListItem[];
  total: number;
}

export interface LocalitiesResponse {
  localities: string[];
}

export interface LteUsageTimelinePoint {
  timestamp: string;
  sites_lte: number;
  sites_fibra: number;
  sites_down: number;
  pct_lte: number;
}

export interface LteUsageTimelineResponse {
  hours: number;
  points: LteUsageTimelinePoint[];
}

export interface LteRankingItem {
  tunnel_name: string;
  site_name: string | null;
  lte_minutes: number;
  fibra_minutes: number;
  down_minutes: number;
  total_minutes: number;
}

export interface LteRankingResponse {
  days: number;
  limit: number;
  items: LteRankingItem[];
}

export interface TunnelCatalog {
  tunnel_name: string;
  site_name: string | null;
  site_address: string | null;
  locality: string | null;
  project_code: string | null;
  contact_person: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SiteCurrentState {
  channel: ChannelType;
  status: string;
  traffic_bytes_per_min: number;
  remote_gateway: string | null;
  proxy_destinations: string[];
}

export interface SitePeriodStats {
  lte_minutes: number;
  fibra_minutes: number;
  down_minutes: number;
  channel_changes: number;
}

export interface SiteDetail {
  tunnel_name: string;
  catalog: TunnelCatalog | null;
  current: SiteCurrentState;
  stats_today: SitePeriodStats;
  stats_week: SitePeriodStats;
}

export interface TrafficHistoryPoint {
  timestamp: string;
  incoming_bytes: number;
  outgoing_bytes: number;
  total_bytes: number;
  bytes_per_min: number;
  channel: ChannelType;
}

export interface TrafficHistoryResponse {
  tunnel_name: string;
  hours: number;
  points: TrafficHistoryPoint[];
}

export interface ChannelTimelineBucket {
  bucket_start: string;
  bucket_end: string;
  channel: ChannelType;
  total_bytes: number;
  bytes_per_min: number;
}

export interface ChannelTimelineResponse {
  tunnel_name: string;
  hours: number;
  buckets: ChannelTimelineBucket[];
}

export interface ChannelEvent {
  timestamp: string;
  from_channel: ChannelType;
  to_channel: ChannelType;
  duration_minutes: number | null;
}

export interface ChannelEventsResponse {
  tunnel_name: string;
  hours: number;
  events: ChannelEvent[];
}

export type SitesFilters = {
  channel?: string;
  locality?: string;
  search?: string;
};

export type TimeRangeHours = 6 | 24 | 168;

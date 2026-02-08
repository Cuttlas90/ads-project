export type RolePreference = 'owner' | 'advertiser'
export type PlacementType = 'post' | 'story'

export interface CampaignSummary {
  id: number
  advertiser_id: number
  title: string
  brief: string
  budget_usdt?: string | null
  budget_ton?: string | null
  preferred_language?: string | null
  start_at?: string | null
  end_at?: string | null
  min_subscribers?: number | null
  min_avg_views?: number | null
  lifecycle_state: string
  max_acceptances: number
  hidden_at?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CampaignPage {
  page: number
  page_size: number
  total: number
  items: CampaignSummary[]
}

export interface CampaignDiscoverItem {
  id: number
  advertiser_id: number
  title: string
  brief: string
  budget_ton?: string | null
  preferred_language?: string | null
  min_subscribers?: number | null
  min_avg_views?: number | null
  max_acceptances: number
  created_at: string
  updated_at: string
}

export interface CampaignDiscoverPage {
  page: number
  page_size: number
  total: number
  items: CampaignDiscoverItem[]
}

export interface CampaignOfferInboxItem {
  application_id: number
  campaign_id: number
  campaign_title: string
  channel_id: number
  channel_username?: string | null
  channel_title?: string | null
  owner_id: number
  proposed_format_label: string
  status: string
  created_at: string
}

export interface CampaignOfferInboxPage {
  page: number
  page_size: number
  total: number
  items: CampaignOfferInboxItem[]
}

export interface CampaignApplicationSummary {
  id: number
  campaign_id: number
  channel_id: number
  owner_id: number
  proposed_format_label: string
  message?: string | null
  status: string
  hidden_at?: string | null
  created_at: string
}

export interface AuthMeResponse {
  id: number
  telegram_user_id: number
  preferred_role: RolePreference | null
  ton_wallet_address: string | null
  has_wallet: boolean
}

export interface UserWalletChallengeResponse {
  challenge: string
  expires_at: string
  ttl_seconds: number
}

export interface TonProofDomainInput {
  lengthBytes: number
  value: string
}

export interface TonProofInput {
  timestamp: number
  domain: TonProofDomainInput
  signature: string
  payload: string
}

export interface TonAccountInput {
  address: string
  chain?: string | null
  walletStateInit?: string | null
  publicKey?: string | null
}

export interface UserWalletVerifyRequest {
  account: TonAccountInput
  proof: TonProofInput
}

export interface UserWalletSummary {
  id: number
  telegram_user_id: number
  ton_wallet_address: string | null
  has_wallet: boolean
}

export interface DealInboxItem {
  id: number
  state: string
  channel_id: number
  channel_username?: string | null
  channel_title?: string | null
  advertiser_id: number
  price_ton: string
  ad_type: string
  updated_at: string
}

export interface DealInboxPage {
  page: number
  page_size: number
  total: number
  items: DealInboxItem[]
}

export interface DealDetail {
  id: number
  source_type: string
  advertiser_id: number
  channel_id: number
  channel_owner_id: number
  listing_id?: number | null
  listing_format_id?: number | null
  campaign_id?: number | null
  campaign_application_id?: number | null
  price_ton: string
  ad_type: string
  placement_type?: PlacementType | null
  exclusive_hours?: number | null
  retention_hours?: number | null
  creative_text: string
  creative_media_type: string
  creative_media_ref: string
  posting_params?: Record<string, unknown> | null
  scheduled_at?: string | null
  verification_window_hours?: number | null
  posted_at?: string | null
  posted_message_id?: string | null
  posted_content_hash?: string | null
  verified_at?: string | null
  state: string
  created_at: string
  updated_at: string
  channel_username?: string | null
  channel_title?: string | null
  advertiser_username?: string | null
  advertiser_first_name?: string | null
  advertiser_last_name?: string | null
}

export interface DealTimelineEvent {
  event_type: string
  from_state?: string | null
  to_state?: string | null
  payload?: Record<string, unknown> | null
  created_at: string
  actor_id?: number | null
}

export interface DealTimelinePage {
  items: DealTimelineEvent[]
  next_cursor?: string | null
}

export interface ChannelSummary {
  id: number
  username?: string | null
  title?: string | null
  is_verified: boolean
  role: string
}

export interface ListingFormatSummary {
  id: number
  listing_id: number
  placement_type: PlacementType
  exclusive_hours: number
  retention_hours: number
  price: string
}

export interface ListingSummary {
  id: number
  channel_id: number
  owner_id: number
  is_active: boolean
}

export interface ListingDetail extends ListingSummary {
  formats: ListingFormatSummary[]
}

export interface ChannelListingResponse {
  has_listing: boolean
  listing?: ListingDetail | null
}

export interface MarketplaceListingFormat {
  id: number
  placement_type: PlacementType
  exclusive_hours: number
  retention_hours: number
  price: string
}

export interface MarketplaceListingItem {
  listing_id: number
  channel_username?: string | null
  channel_title?: string | null
  formats: MarketplaceListingFormat[]
  stats: {
    subscribers?: number | null
    avg_views?: number | null
    premium_ratio: number
  }
}

export interface MarketplaceListingPage {
  page: number
  page_size: number
  total: number
  items: MarketplaceListingItem[]
}

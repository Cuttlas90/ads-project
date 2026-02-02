import { createRouter, createWebHistory } from 'vue-router'

import LandingView from '../views/LandingView.vue'
import OwnerHomeView from '../views/OwnerHomeView.vue'
import AdvertiserHomeView from '../views/AdvertiserHomeView.vue'
import DealDetailView from '../views/DealDetailView.vue'
import ChannelVerifyView from '../views/ChannelVerifyView.vue'
import ListingEditorView from '../views/ListingEditorView.vue'
import OwnerDealsView from '../views/OwnerDealsView.vue'
import OwnerCreativeSubmitView from '../views/OwnerCreativeSubmitView.vue'
import MarketplaceView from '../views/MarketplaceView.vue'
import CampaignCreateView from '../views/CampaignCreateView.vue'
import AdvertiserDealsView from '../views/AdvertiserDealsView.vue'
import AdvertiserCreativeReviewView from '../views/AdvertiserCreativeReviewView.vue'
import FundingView from '../views/FundingView.vue'

const routes = [
  { path: '/', name: 'landing', component: LandingView },
  { path: '/owner', name: 'owner-home', component: OwnerHomeView },
  { path: '/owner/channels/:id/verify', name: 'channel-verify', component: ChannelVerifyView },
  { path: '/owner/channels/:id/listing', name: 'listing-editor', component: ListingEditorView },
  { path: '/owner/deals', name: 'owner-deals', component: OwnerDealsView },
  {
    path: '/owner/deals/:id/creative',
    name: 'owner-creative-submit',
    component: OwnerCreativeSubmitView,
  },
  { path: '/advertiser', name: 'advertiser-home', component: AdvertiserHomeView },
  { path: '/advertiser/marketplace', name: 'marketplace', component: MarketplaceView },
  { path: '/advertiser/campaigns/new', name: 'campaign-create', component: CampaignCreateView },
  { path: '/advertiser/deals', name: 'advertiser-deals', component: AdvertiserDealsView },
  {
    path: '/advertiser/deals/:id/review',
    name: 'advertiser-creative-review',
    component: AdvertiserCreativeReviewView,
  },
  { path: '/advertiser/deals/:id/fund', name: 'funding', component: FundingView },
  { path: '/deals/:id', name: 'deal-detail', component: DealDetailView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

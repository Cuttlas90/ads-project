import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import OwnerHomeView from '../views/OwnerHomeView.vue'
import OwnerCampaignsView from '../views/OwnerCampaignsView.vue'
import DealDetailView from '../views/DealDetailView.vue'
import ChannelVerifyView from '../views/ChannelVerifyView.vue'
import ListingEditorView from '../views/ListingEditorView.vue'
import OwnerDealsView from '../views/OwnerDealsView.vue'
import OwnerCreativeSubmitView from '../views/OwnerCreativeSubmitView.vue'
import MarketplaceView from '../views/MarketplaceView.vue'
import CampaignCreateView from '../views/CampaignCreateView.vue'
import AdvertiserOffersView from '../views/AdvertiserOffersView.vue'
import AdvertiserDealsView from '../views/AdvertiserDealsView.vue'
import AdvertiserCreativeReviewView from '../views/AdvertiserCreativeReviewView.vue'
import FundingView from '../views/FundingView.vue'
import EntryResolverView from '../views/EntryResolverView.vue'
import ProfileView from '../views/ProfileView.vue'
import type { RouteAccess } from './roleAccess'
import { resolveAccessRedirect } from './roleAccess'

interface AppRouteMeta {
  access: RouteAccess
  allowNullRole?: boolean
}

const routeMeta = (access: RouteAccess, allowNullRole = false): AppRouteMeta => ({
  access,
  allowNullRole,
})

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'entry-resolver',
    component: EntryResolverView,
    meta: routeMeta('resolver'),
  },
  {
    path: '/profile',
    name: 'profile',
    component: ProfileView,
    meta: routeMeta('shared', true),
  },
  { path: '/owner', name: 'owner-home', component: OwnerHomeView, meta: routeMeta('owner') },
  {
    path: '/owner/channels/:id/verify',
    name: 'channel-verify',
    component: ChannelVerifyView,
    meta: routeMeta('owner'),
  },
  {
    path: '/owner/channels/:id/listing',
    name: 'listing-editor',
    component: ListingEditorView,
    meta: routeMeta('owner'),
  },
  {
    path: '/owner/campaigns',
    name: 'owner-campaigns',
    component: OwnerCampaignsView,
    meta: routeMeta('owner'),
  },
  { path: '/owner/deals', name: 'owner-deals', component: OwnerDealsView, meta: routeMeta('owner') },
  {
    path: '/owner/deals/:id/creative',
    name: 'owner-creative-submit',
    component: OwnerCreativeSubmitView,
    meta: routeMeta('owner'),
  },
  {
    path: '/advertiser',
    name: 'advertiser-home',
    redirect: '/advertiser/marketplace',
    meta: routeMeta('advertiser'),
  },
  {
    path: '/advertiser/marketplace',
    name: 'marketplace',
    component: MarketplaceView,
    meta: routeMeta('advertiser'),
  },
  {
    path: '/advertiser/campaigns/new',
    name: 'campaign-create',
    component: CampaignCreateView,
    meta: routeMeta('advertiser'),
  },
  {
    path: '/advertiser/offers',
    name: 'advertiser-offers',
    component: AdvertiserOffersView,
    meta: routeMeta('advertiser'),
  },
  {
    path: '/advertiser/deals',
    name: 'advertiser-deals',
    component: AdvertiserDealsView,
    meta: routeMeta('advertiser'),
  },
  {
    path: '/advertiser/deals/:id/review',
    name: 'advertiser-creative-review',
    component: AdvertiserCreativeReviewView,
    meta: routeMeta('advertiser'),
  },
  {
    path: '/advertiser/deals/:id/fund',
    name: 'funding',
    component: FundingView,
    meta: routeMeta('advertiser'),
  },
  {
    path: '/deals/:id',
    name: 'deal-detail',
    component: DealDetailView,
    meta: routeMeta('shared'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: EntryResolverView,
    meta: routeMeta('resolver'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()
  if (!authStore.bootstrapped) {
    await authStore.bootstrap()
  }

  const role = authStore.user?.preferred_role ?? null
  const meta = (to.meta ?? {}) as Partial<AppRouteMeta>
  const access = meta.access ?? 'shared'
  const redirect = resolveAccessRedirect(access, role, Boolean(meta.allowNullRole))

  if (typeof redirect === 'string') {
    if (redirect === to.path) {
      return true
    }
    return redirect
  }
  return true
})

export default router

<template>
  <section class="listing">
    <TgCard title="Listing editor" subtitle="Manage formats and pricing for your channel.">
      <div class="listing__header">
        <TgBadge
          v-if="listingStore.listing"
          :tone="listingStore.listing.is_active ? 'success' : 'warning'"
        >
          {{ listingStore.listing.is_active ? 'Active' : 'Inactive' }}
        </TgBadge>
        <TgButton
          v-if="listingStore.listing"
          variant="ghost"
          size="sm"
          :loading="listingStore.loading"
          @click="toggleActive"
        >
          {{ listingStore.listing.is_active ? 'Deactivate' : 'Activate' }}
        </TgButton>
      </div>

      <TgStatePanel
        v-if="channelsStore.error"
        title="Could not load listing"
        :description="channelsStore.error"
      >
        <template #icon>!</template>
      </TgStatePanel>

      <TgStatePanel
        v-else-if="!listingStore.listing && !channelsStore.loading"
        title="No listing yet"
        description="Create a listing to start selling ad formats."
      >
        <template #icon>✺</template>
        <template #action>
          <TgButton full-width :loading="listingStore.loading" @click="createListing"
            >Create listing</TgButton
          >
        </template>
      </TgStatePanel>

      <div v-else class="listing__body">
        <TgSkeleton v-if="channelsStore.loading" height="80px" />

        <div v-if="listingStore.listing" class="listing__formats">
          <TgList title="Formats" subtitle="Add labels and TON prices.">
            <TgCard v-for="format in listingStore.listing.formats" :key="format.id" :padded="false">
              <div class="listing__format">
                <TgInput v-model="formatEdits[format.id].label" label="Label" />
                <TgInput v-model="formatEdits[format.id].price" label="Price (TON)" type="number" />
                <TgButton
                  size="sm"
                  variant="secondary"
                  :loading="listingStore.loading"
                  @click="saveFormat(format.id)"
                >
                  Save
                </TgButton>
              </div>
            </TgCard>
          </TgList>

          <TgCard title="Add new format" subtitle="Set a label and price for a new placement.">
            <div class="listing__add">
              <TgInput v-model="newFormat.label" label="Label" placeholder="Story, 24h post" />
              <TgInput
                v-model="newFormat.price"
                label="Price (TON)"
                type="number"
                placeholder="0"
              />
              <TgButton full-width :loading="listingStore.loading" @click="addFormat"
                >Add format</TgButton
              >
            </div>
          </TgCard>
        </div>
      </div>
    </TgCard>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, watch } from 'vue'
import { useRoute } from 'vue-router'

import {
  TgBadge,
  TgButton,
  TgCard,
  TgInput,
  TgList,
  TgSkeleton,
  TgStatePanel,
} from '../components/tg'
import { useChannelsStore } from '../stores/channels'
import { useListingsStore } from '../stores/listings'

const route = useRoute()
const channelsStore = useChannelsStore()
const listingStore = useListingsStore()

const channelId = Number(route.params.id)

const newFormat = reactive({
  label: '',
  price: '',
})

const formatEdits = reactive<Record<number, { label: string; price: string }>>({})

const seedFormatEdits = () => {
  if (!listingStore.listing) return
  listingStore.listing.formats.forEach((format) => {
    if (!formatEdits[format.id]) {
      formatEdits[format.id] = { label: format.label, price: format.price }
    }
  })
}

const loadListing = async () => {
  if (!channelId) return
  await channelsStore.fetchListing(channelId)
  if (channelsStore.listing?.has_listing && channelsStore.listing.listing) {
    listingStore.setListing(channelsStore.listing.listing)
    seedFormatEdits()
  } else {
    listingStore.setListing(null)
  }
}

const createListing = async () => {
  if (!channelId) return
  await listingStore.createListing(channelId)
  await loadListing()
}

const addFormat = async () => {
  const label = newFormat.label.trim()
  const price = Number(newFormat.price)
  if (!label || Number.isNaN(price)) return
  await listingStore.addFormat(label, price)
  newFormat.label = ''
  newFormat.price = ''
}

const saveFormat = async (formatId: number) => {
  const edit = formatEdits[formatId]
  if (!edit) return
  const label = edit.label.trim()
  const price = Number(edit.price)
  if (!label || Number.isNaN(price)) return
  const format = listingStore.listing?.formats.find((item) => item.id === formatId)
  if (!format) return
  await listingStore.updateFormat(format, { label, price })
}

const toggleActive = async () => {
  if (!listingStore.listing) return
  await listingStore.updateListing(!listingStore.listing.is_active)
}

watch(
  () => listingStore.listing?.formats.length,
  () => seedFormatEdits(),
)

onMounted(() => {
  void loadListing()
})
</script>

<style scoped>
.listing__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.listing__body {
  display: grid;
  gap: 1rem;
}

.listing__formats {
  display: grid;
  gap: 1rem;
}

.listing__format {
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
}

.listing__add {
  display: grid;
  gap: 0.75rem;
}
</style>

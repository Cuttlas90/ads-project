<template>
  <section class="listing">
    <TgCard title="Listing editor" subtitle="Manage structured ad formats for your channel.">
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
          <TgList
            title="Formats"
            subtitle="Define placement type, exclusivity, retention, and TON price."
          >
            <TgCard v-for="format in listingStore.listing.formats" :key="format.id" :padded="false">
              <div class="listing__format">
                <label class="listing__field">
                  <span>Placement</span>
                  <select v-model="formatEdits[format.id].placement_type" class="listing__select">
                    <option value="post">Post</option>
                    <option value="story">Story</option>
                  </select>
                </label>
                <TgInput
                  v-model="formatEdits[format.id].exclusive_hours"
                  label="Exclusive hours"
                  type="number"
                />
                <TgInput
                  v-model="formatEdits[format.id].retention_hours"
                  label="Retention hours"
                  type="number"
                />
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

          <TgCard title="Add new format" subtitle="Create structured post/story pricing options.">
            <div class="listing__add">
              <label class="listing__field">
                <span>Placement</span>
                <select v-model="newFormat.placement_type" class="listing__select">
                  <option value="post">Post</option>
                  <option value="story">Story</option>
                </select>
              </label>
              <TgInput
                v-model="newFormat.exclusive_hours"
                label="Exclusive hours"
                type="number"
                placeholder="0"
              />
              <TgInput
                v-model="newFormat.retention_hours"
                label="Retention hours"
                type="number"
                placeholder="24"
              />
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
  placement_type: 'post' as 'post' | 'story',
  exclusive_hours: '0',
  retention_hours: '24',
  price: '',
})

const formatEdits = reactive<
  Record<
    number,
    { placement_type: 'post' | 'story'; exclusive_hours: string; retention_hours: string; price: string }
  >
>({})

const parseNonNegativeInt = (value: string) => {
  const parsed = Number(value)
  if (!Number.isInteger(parsed) || parsed < 0) return null
  return parsed
}

const parsePositiveInt = (value: string) => {
  const parsed = Number(value)
  if (!Number.isInteger(parsed) || parsed < 1) return null
  return parsed
}

const parsePrice = (value: string) => {
  const parsed = Number(value)
  if (Number.isNaN(parsed) || parsed < 0) return null
  return parsed
}

const seedFormatEdits = () => {
  if (!listingStore.listing) return
  listingStore.listing.formats.forEach((format) => {
    formatEdits[format.id] = {
      placement_type: format.placement_type,
      exclusive_hours: String(format.exclusive_hours),
      retention_hours: String(format.retention_hours),
      price: format.price,
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
  const exclusiveHours = parseNonNegativeInt(newFormat.exclusive_hours)
  const retentionHours = parsePositiveInt(newFormat.retention_hours)
  const price = parsePrice(newFormat.price)
  if (exclusiveHours === null || retentionHours === null || price === null) return

  await listingStore.addFormat({
    placement_type: newFormat.placement_type,
    exclusive_hours: exclusiveHours,
    retention_hours: retentionHours,
    price,
  })

  newFormat.placement_type = 'post'
  newFormat.exclusive_hours = '0'
  newFormat.retention_hours = '24'
  newFormat.price = ''
}

const saveFormat = async (formatId: number) => {
  const edit = formatEdits[formatId]
  if (!edit) return

  const exclusiveHours = parseNonNegativeInt(edit.exclusive_hours)
  const retentionHours = parsePositiveInt(edit.retention_hours)
  const price = parsePrice(edit.price)
  if (exclusiveHours === null || retentionHours === null || price === null) return

  const format = listingStore.listing?.formats.find((item) => item.id === formatId)
  if (!format) return

  await listingStore.updateFormat(format, {
    placement_type: edit.placement_type,
    exclusive_hours: exclusiveHours,
    retention_hours: retentionHours,
    price,
  })
}

const toggleActive = async () => {
  if (!listingStore.listing) return
  await listingStore.updateListing(!listingStore.listing.is_active)
}

watch(
  () => listingStore.listing?.formats,
  () => seedFormatEdits(),
  { deep: true },
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

.listing__field {
  display: grid;
  gap: 0.35rem;
  font-size: 0.9rem;
}

.listing__field > span {
  color: var(--app-ink-muted);
  font-weight: 600;
}

.listing__select {
  border-radius: var(--app-radius-md);
  border: 1px solid var(--app-border);
  padding: 0.65rem 0.85rem;
  font-size: 0.95rem;
  background: var(--app-surface);
  color: var(--app-ink);
}
</style>

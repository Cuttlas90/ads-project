<template>
  <section class="creative">
    <TgCard title="Submit creative" subtitle="Upload media and send for approval.">
      <TgStatePanel v-if="error" title="Unable to submit" :description="error">
        <template #icon>!</template>
      </TgStatePanel>

      <div class="creative__form">
        <TgInput v-model="creativeText" label="Creative text" placeholder="Write your caption" />

        <label class="creative__upload">
          <span>Media file</span>
          <input type="file" accept="image/*,video/*" :disabled="uploadingMedia || submitting" @change="handleFile" />
        </label>

        <TgBadge v-if="uploadStatus" tone="success">{{ uploadStatus }}</TgBadge>

        <TgButton full-width :loading="uploadingMedia || submitting" :disabled="uploadingMedia" @click="submitCreative"
          >Submit for approval</TgButton
        >
      </div>
    </TgCard>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'

import { TgBadge, TgButton, TgCard, TgInput, TgStatePanel } from '../components/tg'
import { dealsService } from '../services/deals'

const route = useRoute()
const dealId = Number(route.params.id)

const creativeText = ref('')
const creativeMediaType = ref('')
const creativeMediaRef = ref('')
const uploadStatus = ref('')
const uploadingMedia = ref(false)
const submitting = ref(false)
const error = ref('')

const handleFile = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploadingMedia.value = true
  uploadStatus.value = ''
  error.value = ''
  try {
    const response = await dealsService.uploadCreative(dealId, file)
    creativeMediaType.value = response.creative_media_type
    creativeMediaRef.value = response.creative_media_ref
    uploadStatus.value = 'Uploaded to Telegram'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Upload failed'
  } finally {
    uploadingMedia.value = false
  }
}

const submitCreative = async () => {
  if (uploadingMedia.value) {
    return
  }
  if (!creativeText.value.trim() || !creativeMediaRef.value || !creativeMediaType.value) {
    error.value = 'Please add text and upload media before submitting.'
    return
  }
  submitting.value = true
  error.value = ''
  try {
    await dealsService.submitCreative(dealId, {
      creative_text: creativeText.value.trim(),
      creative_media_type: creativeMediaType.value,
      creative_media_ref: creativeMediaRef.value,
    })
    uploadStatus.value = 'Submitted for approval'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Submit failed'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.creative__form {
  display: grid;
  gap: 0.85rem;
}

.creative__upload {
  display: grid;
  gap: 0.4rem;
  font-size: 0.9rem;
  color: var(--app-ink-muted);
}

.creative__upload input {
  border-radius: var(--app-radius-md);
  border: 1px dashed rgba(25, 25, 25, 0.25);
  padding: 0.65rem;
  background: var(--app-surface);
}
</style>

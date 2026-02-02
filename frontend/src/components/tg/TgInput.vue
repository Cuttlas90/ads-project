<template>
  <label class="tg-input">
    <span v-if="label" class="tg-input__label">{{ label }}</span>
    <input
      class="tg-input__field"
      :class="{ 'tg-input__field--error': error }"
      :type="type"
      :placeholder="placeholder"
      :value="modelValue"
      :disabled="disabled"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <span v-if="helper" class="tg-input__helper">{{ helper }}</span>
    <span v-if="error" class="tg-input__error">{{ error }}</span>
  </label>
</template>

<script setup lang="ts">
interface Props {
  modelValue?: string
  label?: string
  placeholder?: string
  type?: string
  helper?: string
  error?: string
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  modelValue: '',
  type: 'text',
  disabled: false,
})

defineEmits<{ 'update:modelValue': [value: string] }>()
</script>

<style scoped>
.tg-input {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.9rem;
}

.tg-input__label {
  color: var(--app-ink-muted);
  font-weight: 600;
}

.tg-input__field {
  border-radius: var(--app-radius-md);
  border: 1px solid var(--app-border);
  padding: 0.65rem 0.85rem;
  font-size: 0.95rem;
  background: var(--app-surface);
  color: var(--app-ink);
  outline: none;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.tg-input__field:focus {
  border-color: var(--app-accent);
  box-shadow: 0 0 0 3px rgba(11, 122, 117, 0.15);
}

.tg-input__field--error {
  border-color: var(--app-danger);
  box-shadow: 0 0 0 3px rgba(214, 69, 80, 0.12);
}

.tg-input__helper {
  color: var(--app-ink-muted);
  font-size: 0.8rem;
}

.tg-input__error {
  color: var(--app-danger);
  font-size: 0.8rem;
  font-weight: 600;
}
</style>

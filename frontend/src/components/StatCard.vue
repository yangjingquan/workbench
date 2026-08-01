<template><div class="stat-card"><div class="stat-label">{{ label }}<span :class="['stat-icon', tone]">{{ icon }}</span></div><div class="stat-value">{{ value }}</div><div class="stat-foot"><span :class="trend > 0 ? 'up' : 'muted'">{{ trend ? `${trend > 0 ? '+' : ''}${trend}%` : '—' }}</span><span>{{ foot }}</span></div></div></template>
<script setup>defineProps({ label: String, value: [String, Number], foot: String, trend: Number, icon: String, tone: String })</script>


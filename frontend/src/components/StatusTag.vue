<template><span :class="['status-tag', tone]">{{ label || text }}</span></template>
<script setup>defineProps({ text: String, label: String, tone: { type: String, default: '' } })</script>


<template><el-select v-bind="$attrs"><el-option v-for="item in options" :key="item.value ?? item" :label="item.label ?? item" :value="item.value ?? item"/></el-select></template>
<script setup>defineProps({ options: { type: Array, default: () => [] } })</script>


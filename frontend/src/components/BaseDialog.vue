<template><el-dialog v-bind="$attrs" :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)"><slot/><template #footer><slot name="footer"/></template></el-dialog></template>
<script setup>defineProps({ modelValue: Boolean }); defineEmits(['update:modelValue'])</script>


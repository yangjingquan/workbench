<template>
  <div class="page-heading"><div><h1>开发工具箱</h1><p>轻量、本地优先。每次使用会记录到统计看板，不上传工具内容。</p></div></div>
  <div class="tool-grid">
    <div class="panel tool-box"><div class="panel-header"><div><div class="panel-title">JSON 格式化 / 压缩 / 校验</div><div class="panel-subtitle">在浏览器本地完成计算</div></div></div><el-input v-model="jsonText" type="textarea" placeholder='{"hello":"workbench"}'/><div class="tool-actions"><el-button type="primary" @click="jsonFormat">格式化</el-button><el-button @click="jsonMinify">压缩</el-button><el-button @click="jsonValidate">校验</el-button></div></div>
    <div class="panel tool-box"><div class="panel-header"><div><div class="panel-title">Base64 编码 / 解码</div><div class="panel-subtitle">适用于文本片段</div></div></div><el-input v-model="baseText" type="textarea"/><div class="tool-actions"><el-button type="primary" @click="baseEncode">编码</el-button><el-button @click="baseDecode">解码</el-button></div></div>
    <div class="panel tool-box"><div class="panel-header"><div><div class="panel-title">时间戳转换</div><div class="panel-subtitle">支持秒级 / 毫秒级时间戳与本地标准日期</div></div></div><div class="timestamp-fields"><div><label>时间戳</label><el-input v-model="timestampValue" placeholder="10 位秒级或 13 位毫秒级" /></div><div><label>标准日期</label><el-input v-model="dateValue" placeholder="YYYY-MM-DD HH:mm:ss" /></div></div><div class="tool-actions"><el-button type="primary" @click="toDate">时间戳 → 日期</el-button><el-button @click="toTimestamp">日期 → 时间戳</el-button></div></div>
    <div class="panel tool-box"><div class="panel-header"><div><div class="panel-title">URL 编码 / 解码</div><div class="panel-subtitle">处理查询参数和路径片段</div></div></div><el-input v-model="urlText" type="textarea"/><div class="tool-actions"><el-button type="primary" @click="urlEncode">编码</el-button><el-button @click="urlDecode">解码</el-button></div></div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/http'

const jsonText = ref(''); const baseText = ref(''); const timestampValue = ref(String(Math.floor(Date.now() / 1000))); const dateValue = ref(''); const urlText = ref('')
const log = action => api.usage({ tool_name: 'toolkit', action }).catch(() => {})
function jsonFormat() { try { jsonText.value = JSON.stringify(JSON.parse(jsonText.value), null, 2); log('json_format') } catch { ElMessage.error('JSON 格式不正确') } }
function jsonMinify() { try { jsonText.value = JSON.stringify(JSON.parse(jsonText.value)); log('json_minify') } catch { ElMessage.error('JSON 格式不正确') } }
function jsonValidate() { try { JSON.parse(jsonText.value); ElMessage.success('JSON 有效'); log('json_validate') } catch { ElMessage.error('JSON 无效'); log('json_validate') } }
function baseEncode() { baseText.value = btoa(unescape(encodeURIComponent(baseText.value))); log('base64_encode') }
function baseDecode() { try { baseText.value = decodeURIComponent(escape(atob(baseText.value))); log('base64_decode') } catch { ElMessage.error('Base64 无效') } }
function pad(value) { return String(value).padStart(2, '0') }
function formatLocalDate(date) { return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}` }
function toDate() { const raw = timestampValue.value.trim(); const number = Number(raw); if (!raw || !Number.isFinite(number)) return ElMessage.error('请输入有效时间戳'); dateValue.value = formatLocalDate(new Date(raw.length === 10 ? number * 1000 : number)); log('timestamp_to_date') }
function toTimestamp() { const date = new Date(dateValue.value.trim().replace(' ', 'T')); if (Number.isNaN(date.getTime())) return ElMessage.error('请输入 YYYY-MM-DD HH:mm:ss 格式日期'); timestampValue.value = String(Math.floor(date.getTime() / 1000)); log('date_to_timestamp') }
function urlEncode() { urlText.value = encodeURIComponent(urlText.value); log('url_encode') }
function urlDecode() { try { urlText.value = decodeURIComponent(urlText.value); log('url_decode') } catch { ElMessage.error('URL 编码无效') } }
</script>

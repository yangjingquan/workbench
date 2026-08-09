function streamUrl(containerId, params = {}) {
  const base = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => { if (value !== undefined && value !== null && value !== '') query.set(key, value) })
  const suffix = query.toString() ? `?${query.toString()}` : ''
  return `${base}/api/docker/containers/${encodeURIComponent(containerId)}/logs/stream${suffix}`
}

function errorMessage(payload, fallback) {
  return payload?.detail || payload?.msg || fallback
}

export async function streamDockerLogs(containerId, params = {}, onEvent, signal) {
  const token = localStorage.getItem('workbench_token')
  const response = await fetch(streamUrl(containerId, params), { headers: token ? { Authorization: `Bearer ${token}` } : {}, signal })
  if (!response.ok) {
    let payload = null
    try { payload = await response.json() } catch { /* Keep the HTTP fallback below. */ }
    throw new Error(errorMessage(payload, '日志流连接失败'))
  }
  if (!response.body) return
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  const consume = record => {
    const data = record.split(/\r?\n/).filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n')
    if (data) onEvent(JSON.parse(data))
  }
  while (true) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
    const records = buffer.split(/\r?\n\r?\n/)
    buffer = records.pop() || ''
    records.filter(Boolean).forEach(consume)
    if (done) break
  }
  if (buffer.trim()) consume(buffer)
}

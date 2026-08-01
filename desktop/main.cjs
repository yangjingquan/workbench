const { app, BrowserWindow, dialog, shell } = require('electron')
const fs = require('node:fs')
const path = require('node:path')
const { spawn } = require('node:child_process')
const http = require('node:http')

const API_URL = 'http://127.0.0.1:8100'
let mainWindow
let backendProcess

function isExternalUrl(value) {
  try {
    const url = new URL(value)
    return ['http:', 'https:', 'mailto:', 'tel:'].includes(url.protocol)
  } catch {
    return false
  }
}

function openInDefaultBrowser(value) {
  if (isExternalUrl(value)) shell.openExternal(value)
}

function backendIsReady() {
  return new Promise(resolve => {
    const request = http.get(`${API_URL}/health`, response => {
      response.resume()
      resolve(response.statusCode === 200)
    })
    request.on('error', () => resolve(false))
    request.setTimeout(1000, () => { request.destroy(); resolve(false) })
  })
}

function backendCandidates() {
  const backendDir = app.isPackaged ? path.join(process.resourcesPath, 'backend') : path.resolve(__dirname, '../backend')
  const bundledExecutable = path.join(backendDir, 'workbench-api')
  const localPython = path.join(backendDir, '.venv', 'bin', 'python')
  return [
    { command: bundledExecutable, args: [], cwd: backendDir },
    { command: process.env.WORKBENCH_PYTHON || localPython, args: ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8100'], cwd: backendDir },
    { command: 'python3', args: ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8100'], cwd: backendDir },
  ].filter(item => item.command === 'python3' || fs.existsSync(item.command))
}

async function startBackendIfNeeded() {
  if (await backendIsReady()) return true
  const candidate = backendCandidates()[0]
  if (!candidate) return false
  backendProcess = spawn(candidate.command, candidate.args, { cwd: candidate.cwd, stdio: 'ignore' })
  backendProcess.on('error', error => console.error('Workbench backend failed to start:', error.message))
  for (let attempt = 0; attempt < 20; attempt += 1) {
    if (await backendIsReady()) return true
    await new Promise(resolve => setTimeout(resolve, 300))
  }
  return false
}

function configureExternalNavigation(window) {
  window.webContents.setWindowOpenHandler(({ url }) => {
    openInDefaultBrowser(url)
    return { action: 'deny' }
  })
  window.webContents.on('will-navigate', (event, url) => {
    if (!isExternalUrl(url)) return
    const current = window.webContents.getURL()
    if (current && new URL(url).origin === new URL(current).origin) return
    event.preventDefault()
    openInDefaultBrowser(url)
  })
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 1080,
    minHeight: 720,
    backgroundColor: '#f5f7fb',
    title: 'Workbench',
    webPreferences: { contextIsolation: true, nodeIntegration: false, preload: path.join(__dirname, 'preload.cjs') },
  })
  configureExternalNavigation(mainWindow)
  const renderer = path.join(__dirname, 'renderer', 'index.html')
  await mainWindow.loadFile(renderer)
  if (!backendProcess && !(await backendIsReady())) {
    dialog.showMessageBox(mainWindow, { type: 'warning', title: '后端服务未启动', message: 'Workbench 客户端已打开，但本机 FastAPI 后端或 MySQL 未启动。请先启动后端服务后刷新页面。' })
  }
}

app.whenReady().then(async () => {
  await startBackendIfNeeded()
  await createWindow()
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow() })
})

app.on('window-all-closed', () => {
  if (backendProcess && !backendProcess.killed) backendProcess.kill()
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => {
  if (backendProcess && !backendProcess.killed) backendProcess.kill()
})

const { contextBridge } = require('electron')

// 目前页面不需要 Node 能力，保留隔离的 preload 作为后续桌面能力扩展入口。
contextBridge.exposeInMainWorld('workbenchDesktop', { platform: process.platform })

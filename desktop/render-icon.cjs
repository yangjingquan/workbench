const { app, BrowserWindow } = require('electron')
const fs = require('node:fs')
const path = require('node:path')

const source = process.argv[2]
const output = process.argv[3]
const sizes = [16, 32, 128, 256, 512]
const svg = fs.readFileSync(source, 'utf8')
const dataUrl = `data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}`

app.whenReady().then(async () => {
  const window = new BrowserWindow({
    width: 1024,
    height: 1024,
    show: false,
    transparent: true,
    webPreferences: { offscreen: true },
  })
  const html = `<style>html,body{margin:0;width:1024px;height:1024px;background:transparent;overflow:hidden}img{display:block;width:1024px;height:1024px}</style><img src="${dataUrl}" />`
  await window.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`)
  await new Promise(resolve => setTimeout(resolve, 300))
  const image = await window.webContents.capturePage({ x: 0, y: 0, width: 1024, height: 1024 })
  fs.mkdirSync(output, { recursive: true })
  for (const size of sizes) {
    fs.writeFileSync(path.join(output, `icon_${size}x${size}.png`), image.resize({ width: size, height: size }).toPNG())
    fs.writeFileSync(path.join(output, `icon_${size}x${size}@2x.png`), image.resize({ width: size * 2, height: size * 2 }).toPNG())
  }
  window.destroy()
  app.quit()
})

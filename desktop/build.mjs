import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const desktopDir = path.dirname(fileURLToPath(import.meta.url))
const sourceDir = path.resolve(desktopDir, '../frontend/dist')
const targetDir = path.resolve(desktopDir, 'renderer')

if (!fs.existsSync(sourceDir)) throw new Error(`Frontend build not found: ${sourceDir}`)
fs.rmSync(targetDir, { recursive: true, force: true })
fs.cpSync(sourceDir, targetDir, { recursive: true })
console.log(`Renderer copied to ${targetDir}`)

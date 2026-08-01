import assert from 'node:assert/strict'
import { generateKeyPairSync, privateDecrypt, constants } from 'node:crypto'
import test from 'node:test'
import { encryptPassword } from './rsa.js'

test('encryptPassword supports RSA-OAEP when Web Crypto is unavailable', async () => {
  const { publicKey, privateKey } = generateKeyPairSync('rsa', { modulusLength: 2048 })
  const publicPem = publicKey.export({ type: 'spki', format: 'pem' })

  const ciphertext = await encryptPassword('admin123', publicPem, { forceFallback: true })
  const plaintext = privateDecrypt(
    { key: privateKey, padding: constants.RSA_PKCS1_OAEP_PADDING, oaepHash: 'sha256' },
    Buffer.from(ciphertext, 'base64'),
  ).toString('utf8')

  assert.equal(plaintext, 'admin123')
})

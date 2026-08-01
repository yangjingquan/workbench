const SHA256_K = [
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]

function rotr(value, amount) {
  return (value >>> amount) | (value << (32 - amount))
}

function sha256(input) {
  const bytes = input instanceof Uint8Array ? input : new TextEncoder().encode(input)
  const paddedLength = Math.ceil((bytes.length + 9) / 64) * 64
  const padded = new Uint8Array(paddedLength)
  padded.set(bytes)
  padded[bytes.length] = 0x80
  const view = new DataView(padded.buffer)
  view.setUint32(paddedLength - 4, bytes.length * 8)

  let h0 = 0x6a09e667; let h1 = 0xbb67ae85; let h2 = 0x3c6ef372; let h3 = 0xa54ff53a
  let h4 = 0x510e527f; let h5 = 0x9b05688c; let h6 = 0x1f83d9ab; let h7 = 0x5be0cd19

  for (let offset = 0; offset < padded.length; offset += 64) {
    const words = new Uint32Array(64)
    for (let index = 0; index < 16; index += 1) words[index] = view.getUint32(offset + index * 4)
    for (let index = 16; index < 64; index += 1) {
      const s0 = rotr(words[index - 15], 7) ^ rotr(words[index - 15], 18) ^ (words[index - 15] >>> 3)
      const s1 = rotr(words[index - 2], 17) ^ rotr(words[index - 2], 19) ^ (words[index - 2] >>> 10)
      words[index] = (words[index - 16] + s0 + words[index - 7] + s1) >>> 0
    }

    let a = h0; let b = h1; let c = h2; let d = h3; let e = h4; let f = h5; let g = h6; let h = h7
    for (let index = 0; index < 64; index += 1) {
      const s1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)
      const choose = (e & f) ^ (~e & g)
      const temp1 = (h + s1 + choose + SHA256_K[index] + words[index]) >>> 0
      const s0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)
      const majority = (a & b) ^ (a & c) ^ (b & c)
      const temp2 = (s0 + majority) >>> 0
      h = g; g = f; f = e; e = (d + temp1) >>> 0; d = c; c = b; b = a; a = (temp1 + temp2) >>> 0
    }
    h0 = (h0 + a) >>> 0; h1 = (h1 + b) >>> 0; h2 = (h2 + c) >>> 0; h3 = (h3 + d) >>> 0
    h4 = (h4 + e) >>> 0; h5 = (h5 + f) >>> 0; h6 = (h6 + g) >>> 0; h7 = (h7 + h) >>> 0
  }

  const result = new Uint8Array(32)
  const output = new DataView(result.buffer)
  ;[h0, h1, h2, h3, h4, h5, h6, h7].forEach((value, index) => output.setUint32(index * 4, value))
  return result
}

function concatBytes(...chunks) {
  const result = new Uint8Array(chunks.reduce((total, chunk) => total + chunk.length, 0))
  let offset = 0
  chunks.forEach(chunk => { result.set(chunk, offset); offset += chunk.length })
  return result
}

function mgf1(seed, length) {
  const result = new Uint8Array(length)
  for (let counter = 0, offset = 0; offset < length; counter += 1) {
    const counterBytes = new Uint8Array([(counter >>> 24) & 0xff, (counter >>> 16) & 0xff, (counter >>> 8) & 0xff, counter & 0xff])
    const digest = sha256(concatBytes(seed, counterBytes))
    result.set(digest.slice(0, Math.min(digest.length, length - offset)), offset)
    offset += digest.length
  }
  return result
}

function randomBytes(length) {
  const result = new Uint8Array(length)
  if (!globalThis.crypto?.getRandomValues) throw new Error('当前浏览器不支持安全随机数，无法加密登录密码')
  return globalThis.crypto.getRandomValues(result)
}

function readDerTlv(bytes, offset) {
  const tag = bytes[offset]
  let length = bytes[offset + 1]
  let valueStart = offset + 2
  if (length & 0x80) {
    const size = length & 0x7f
    length = 0
    for (let index = 0; index < size; index += 1) length = (length << 8) | bytes[valueStart + index]
    valueStart += size
  }
  return { tag, valueStart, valueEnd: valueStart + length, next: valueStart + length }
}

function pemToBytes(pem) {
  const base64 = pem.replace(/-----(BEGIN|END) PUBLIC KEY-----/g, '').replace(/\s/g, '')
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index)
  return bytes
}

function parseRsaPublicKey(pem) {
  const spki = pemToBytes(pem)
  const outer = readDerTlv(spki, 0)
  const algorithm = readDerTlv(spki, outer.valueStart)
  const bitString = readDerTlv(spki, algorithm.next)
  const rsaDer = spki.slice(bitString.valueStart + 1, bitString.valueEnd)
  const rsaSequence = readDerTlv(rsaDer, 0)
  const modulus = readDerTlv(rsaDer, rsaSequence.valueStart)
  const exponent = readDerTlv(rsaDer, modulus.next)
  const modulusBytes = rsaDer.slice(modulus.valueStart, modulus.valueEnd)[0] === 0 ? rsaDer.slice(modulus.valueStart + 1, modulus.valueEnd) : rsaDer.slice(modulus.valueStart, modulus.valueEnd)
  const exponentBytes = rsaDer.slice(exponent.valueStart, exponent.valueEnd)
  const toBigInt = bytes => bytes.reduce((value, byte) => (value << 8n) | BigInt(byte), 0n)
  const n = toBigInt(modulusBytes)
  return { n, e: toBigInt(exponentBytes), keyLength: Math.ceil(n.toString(2).length / 8) }
}

function toFixedBytes(value, length) {
  const result = new Uint8Array(length)
  for (let index = length - 1; index >= 0; index -= 1) { result[index] = Number(value & 0xffn); value >>= 8n }
  return result
}

function modPow(base, exponent, modulus) {
  let result = 1n
  base %= modulus
  while (exponent > 0n) {
    if (exponent & 1n) result = (result * base) % modulus
    base = (base * base) % modulus
    exponent >>= 1n
  }
  return result
}

function encryptWithFallback(password, pem) {
  const { n, e, keyLength } = parseRsaPublicKey(pem)
  const message = new TextEncoder().encode(password)
  const hashLength = 32
  if (message.length > keyLength - 2 * hashLength - 2) throw new Error('密码长度超过加密限制')
  const seed = randomBytes(hashLength)
  const db = new Uint8Array(keyLength - hashLength - 1)
  db.set(sha256(new Uint8Array(0)))
  db[db.length - message.length - 1] = 1
  db.set(message, db.length - message.length)
  const dbMask = mgf1(seed, db.length)
  const maskedDb = db.map((value, index) => value ^ dbMask[index])
  const seedMask = mgf1(maskedDb, hashLength)
  const maskedSeed = seed.map((value, index) => value ^ seedMask[index])
  const encoded = concatBytes(new Uint8Array([0]), maskedSeed, maskedDb)
  const encrypted = toFixedBytes(modPow(encoded.reduce((value, byte) => (value << 8n) | BigInt(byte), 0n), e, n), keyLength)
  let binary = ''
  encrypted.forEach(byte => { binary += String.fromCharCode(byte) })
  return btoa(binary)
}

export async function encryptPassword(password, pem, options = {}) {
  const subtle = globalThis.crypto?.subtle
  if (!options.forceFallback && subtle?.importKey && subtle?.encrypt) {
    const key = await subtle.importKey('spki', pemToBytes(pem).buffer, { name: 'RSA-OAEP', hash: 'SHA-256' }, false, ['encrypt'])
    const encrypted = await subtle.encrypt({ name: 'RSA-OAEP' }, key, new TextEncoder().encode(password))
    let binary = ''
    new Uint8Array(encrypted).forEach(byte => { binary += String.fromCharCode(byte) })
    return btoa(binary)
  }
  return encryptWithFallback(password, pem)
}

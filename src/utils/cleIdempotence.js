// UUID v4 à partir de l'entropie navigateur, y compris sans crypto.randomUUID.
export function cleIdempotence() {
  const octets = globalThis.crypto.getRandomValues(new Uint8Array(16))
  octets[6] = (octets[6] & 0x0f) | 0x40
  octets[8] = (octets[8] & 0x3f) | 0x80
  const h = Array.from(octets, n => n.toString(16).padStart(2, '0')).join('')
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`
}

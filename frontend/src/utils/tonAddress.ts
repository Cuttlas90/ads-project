const RAW_TON_ADDRESS_PATTERN = /^(-?\d+):([0-9a-fA-F]{64})$/

interface FriendlyAddressOptions {
  testOnly?: boolean
}

// Convert raw TON address (workchain:hex) into bounceable user-friendly form used by wallets.
export const toWalletFriendlyAddress = (
  rawAddress: string,
  options: FriendlyAddressOptions = {},
): string => {
  const normalized = rawAddress.trim()
  const match = normalized.match(RAW_TON_ADDRESS_PATTERN)
  if (!match) {
    return normalized
  }

  const workchain = Number(match[1])
  if (!Number.isInteger(workchain) || workchain < -128 || workchain > 127) {
    return normalized
  }

  const hashHex = match[2]
  const hashBytes = new Uint8Array(32)
  for (let i = 0; i < 32; i += 1) {
    const byteValue = Number.parseInt(hashHex.slice(i * 2, i * 2 + 2), 16)
    if (Number.isNaN(byteValue)) {
      return normalized
    }
    hashBytes[i] = byteValue
  }

  let tag = 0x11 // bounceable
  if (options.testOnly) {
    tag |= 0x80
  }

  const body = new Uint8Array(34)
  body[0] = tag
  body[1] = workchain < 0 ? 256 + workchain : workchain
  body.set(hashBytes, 2)

  const crc = crc16Xmodem(body)
  const full = new Uint8Array(36)
  full.set(body, 0)
  full.set(crc, 34)

  return toBase64Url(full)
}

const crc16Xmodem = (data: Uint8Array): Uint8Array => {
  let crc = 0

  for (const byte of data) {
    crc ^= byte << 8
    for (let i = 0; i < 8; i += 1) {
      if ((crc & 0x8000) !== 0) {
        crc = ((crc << 1) ^ 0x1021) & 0xffff
      } else {
        crc = (crc << 1) & 0xffff
      }
    }
  }

  return new Uint8Array([(crc >> 8) & 0xff, crc & 0xff])
}

const toBase64Url = (bytes: Uint8Array): string => {
  if (typeof btoa !== 'function') {
    throw new Error('Base64 encoder is unavailable in this environment')
  }

  let binary = ''
  for (const byte of bytes) {
    binary += String.fromCharCode(byte)
  }

  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '')
}

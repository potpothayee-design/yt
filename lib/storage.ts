import type { GalleryItem } from './types'

/**
 * Gallery persistence. Blobs live in IndexedDB so a refresh never loses work
 * and downloads never need to re-hit the network.
 */
const DB_NAME = 'tiny-workers-studio'
const DB_VERSION = 1
const STORE = 'assets'

interface StoredRecord extends Omit<GalleryItem, 'url'> {
  blob: Blob
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      reject(new Error('IndexedDB unavailable'))
      return
    }
    const req = indexedDB.open(DB_NAME, DB_VERSION)
    req.onupgradeneeded = () => {
      const db = req.result
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: 'id' })
        store.createIndex('createdAt', 'createdAt')
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

export async function saveAsset(item: GalleryItem, blob: Blob): Promise<void> {
  try {
    const db = await openDb()
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite')
      const { url: _url, ...rest } = item
      tx.objectStore(STORE).put({ ...rest, blob } as StoredRecord)
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error)
    })
    db.close()
  } catch {
    /* Storage is a nice-to-have; never block a generation on it. */
  }
}

export async function loadAssets(): Promise<GalleryItem[]> {
  try {
    const db = await openDb()
    const records = await new Promise<StoredRecord[]>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readonly')
      const req = tx.objectStore(STORE).getAll()
      req.onsuccess = () => resolve(req.result as StoredRecord[])
      req.onerror = () => reject(req.error)
    })
    db.close()
    return records
      .sort((a, b) => b.createdAt - a.createdAt)
      .map(({ blob, ...rest }) => ({ ...rest, url: URL.createObjectURL(blob) }))
  } catch {
    return []
  }
}

export async function getBlob(id: string): Promise<Blob | null> {
  try {
    const db = await openDb()
    const rec = await new Promise<StoredRecord | undefined>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readonly')
      const req = tx.objectStore(STORE).get(id)
      req.onsuccess = () => resolve(req.result as StoredRecord | undefined)
      req.onerror = () => reject(req.error)
    })
    db.close()
    return rec?.blob ?? null
  } catch {
    return null
  }
}

export async function deleteAsset(id: string): Promise<void> {
  try {
    const db = await openDb()
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite')
      tx.objectStore(STORE).delete(id)
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error)
    })
    db.close()
  } catch {
    /* ignore */
  }
}

export async function clearAssets(): Promise<void> {
  try {
    const db = await openDb()
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite')
      tx.objectStore(STORE).clear()
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error)
    })
    db.close()
  } catch {
    /* ignore */
  }
}

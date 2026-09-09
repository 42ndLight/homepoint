import Dexie from 'dexie'

const db = new Dexie('HomePointDB')

db.version(1).stores({
  categories: '++id, name, slug, parent_id',
  products: '++id, name, slug, category_id, base_price, is_active',
  variants: '++id, product_id, sku, price, unit_type, stock_threshold, *attributes',
  inventory: '++id, variant_id, quantity, last_updated, location',
  syncMetadata: '++id, table_name, last_sync',
})

export default db

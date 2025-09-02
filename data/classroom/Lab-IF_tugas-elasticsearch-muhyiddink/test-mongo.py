from pymongo import MongoClient

# Coba membuat koneksi ke MongoDB
try:
    mongo_client = MongoClient('mongodb://root:if20222@if.unismuh.ac.id:27222/')
    db = mongo_client['latihan']
    koleksi = db['people']

    # Cek status koneksi
    is_connected = mongo_client.server_info() is not None
    if is_connected:
        print("Berhasil terhubung ke MongoDB")
    else:
        print("Gagal terhubung ke MongoDB")

    # Tutup koneksi ke MongoDB
    mongo_client.close()

except Exception as e:
    print("Gagal terhubung ke MongoDB:", str(e))

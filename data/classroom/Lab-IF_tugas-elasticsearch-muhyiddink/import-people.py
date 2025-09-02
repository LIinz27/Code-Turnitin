from pymongo import MongoClient
from elasticsearch import Elasticsearch
from bson import ObjectId
from tqdm import tqdm
import json

# Coba membuat koneksi ke MongoDB
try:
    # Koneksi ke MongoDB
    mongo_client = MongoClient('mongodb://if:samasemua@if.unismuh.ac.id:27222/')
    db = mongo_client['latihan']
    koleksi = db['popular_peoples']

    # Cek status koneksi ke MongoDB
    is_connected = mongo_client.server_info() is not None
    if is_connected:
        print("Berhasil terhubung ke MongoDB")
    else:
        print("Gagal terhubung ke MongoDB")
        exit()

    # Koneksi ke Elasticsearch
    es = Elasticsearch('http://localhost:9200/')

    # Hitung total data MongoDB
    total_data = koleksi.count_documents({})

    # Query data dari MongoDB
    data_mongodb = koleksi.find({})

    # Import data ke Elasticsearch
    with tqdm(total=total_data, desc="Importing Data", unit="doc") as pbar:
        for data in data_mongodb:
            # Menghapus field _id
            data.pop('_id')

            # Mengimpor data ke Elasticsearch
            es.index(index='people', document=json.loads(json.dumps(data)))
            pbar.update(1)

    print("Pengimporan data selesai")

    # Tutup koneksi ke MongoDB
    mongo_client.close()

except Exception as e:
    print("Gagal terhubung ke MongoDB:", str(e))

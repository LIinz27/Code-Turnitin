const fs = require('fs'); // Mengimpor modul bawaan Node.js 'fs' untuk operasi sistem berkas.
const path = require('path'); // Mengimpor modul bawaan Node.js 'path' untuk bekerja dengan jalur berkas.
const axios = require('axios'); // Mengimpor pustaka 'axios' untuk melakukan permintaan HTTP.

// Mendefinisikan fungsi asinkron untuk mengunduh berkas dari URL yang diberikan.
const downloadFile = async (url) => {
  // Mengirim permintaan HTTP GET ke URL yang diberikan dan mendapatkan respons dengan tipe respons berupa aliran (stream).
  const response = await axios({
    url,
    method: 'GET',
    responseType: 'stream',
  });

  // Menyimpan tipe konten dari header respons.
  const contentType = response.headers['content-type'];
  // Mendapatkan ekstensi berkas dari tipe konten.
  const fileExtension = contentType.split('/')[1];

  // Membuat nama berkas unik berdasarkan penanda waktu saat ini dan ekstensi berkas.
  const fileName = `downloaded_${Date.now()}.${fileExtension}`;
  // Mengatur jalur tujuan untuk menyimpan berkas yang diunduh menggunakan modul 'path'.
  const destination = path.join(__dirname, 'downloads', fileName);

  // Membuat aliran yang dapat ditulis untuk menyimpan data yang diunduh ke berkas tujuan.
  const writer = fs.createWriteStream(destination);

  // Mengarahkan (mengalirkan) aliran data dari respons HTTP ke aliran penulis untuk menyimpan berkas.
  response.data.pipe(writer);

  // Mengembalikan sebuah janji (promise) yang akan diselesaikan saat penulis selesai menulis atau ditolak jika terjadi kesalahan.
  return new Promise((resolve, reject) => {
    writer.on('finish', resolve);
    writer.on('error', reject);
  });
};

// Daftar URL berkas yang akan diunduh.
const filesToDownload = [
  'https://cdn.discordapp.com/attachments/971002262300282880/1113367543088959488/00015-17325760.png',
  'https://cdn.discordapp.com/attachments/971002262300282880/1115131596526338090/00039-700412126.png',
];

// Mendefinisikan fungsi asinkron untuk mengunduh semua berkas dalam array 'filesToDownload'.
const downloadAllFiles = async () => {
  // Membuat direktori 'downloads' jika belum ada, dengan opsi rekursif untuk membuat direktori bersarang.
  fs.mkdirSync(path.join(__dirname, 'downloads'), { recursive: true });

  // Membuat array janji (promises) untuk mengunduh setiap berkas dalam 'filesToDownload'.
  const downloadPromises = filesToDownload.map(async (url) => {
    try {
      console.log(`Mengunduh ${url}`);
      await downloadFile(url); // Menunggu hingga berkas selesai diunduh.
      console.log(`Berhasil mengunduh ${url}`);
    } catch (error) {
      console.error(`Kesalahan saat mengunduh ${url}: ${error.message}`);
    }
  });

  // Menunggu hingga semua janji pengunduhan selesai, lalu mencetak pesan selesai.
  await Promise.all(downloadPromises);
  console.log('Semua pengunduhan selesai.');
};

// Memanggil fungsi 'downloadAllFiles' untuk memulai proses pengunduhan.
downloadAllFiles();

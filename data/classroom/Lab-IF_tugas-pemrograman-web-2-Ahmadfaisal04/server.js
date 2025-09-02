const http = require('http');

const server = http.createServer((request, response) => {
  const parsedUrl = new URL(request.url, `${request.protocol}://${request.headers.host}`);
  const params = parsedUrl.searchParams;

  if (parsedUrl.pathname === "/") {
    try {
      const nama = params.get("nama");
      const nim = params.get("nim");

      if (!nama || !nim) {
        response.statusCode = 400;
        response.setHeader("Content-Type", "text/html");
        response.write("Harap masukkan nama dan nim.");
        response.end();
        return;
      }

      if (isNaN(nim)) {
        response.statusCode = 400;
        response.setHeader("Content-Type", "text/html");
        response.write("NIM harus berupa angka.");
        response.end();
        return;
      }

      response.statusCode = 200;
      response.setHeader("Content-Type", "text/html");
      response.write("Nama mahasiswa: " + nama);
      response.write("<br>");
      response.write("NIM mahasiswa: " + nim);
      response.write("<br>");
      response.write(`<img src="https://simak.unismuh.ac.id/upload/mahasiswa/${nim}_.jpg" alt="Foto mahasiswa dengan NIM ${nim}" width="200" height="200">`);
      response.end();
    } catch (error) {
      console.error(error);
      response.statusCode = 500;
      response.setHeader("Content-Type", "text/html");
      response.write("Terjadi kesalahan pada server.");
      response.end();
    }
  } else {
    response.statusCode = 404;
    response.setHeader("Content-Type", "text/html");
    response.write("Halaman tidak ditemukan.");
    response.end();
  }
});

server.on('error', (error) => {
  console.error(error);
});

server.listen(8080, () => {
  console.log('Server is running on port 8080');
});

const http = require("http");
const url = require("url");

const hostname = "127.0.0.1";
const port = 3000;

const server = http.createServer((request, response) => {
  const parsedUrl = new URL(request.url, `http://${request.headers.host}`);

  if (parsedUrl.pathname === "/") {
    response.statusCode = 200;
    response.setHeader("Content-Type", "text/html");
    response.end("Ini Halaman Utama <b>Informatika 2021 A</b>");

  }
  else if (parsedUrl.pathname === "/profile"){
    nim = parsedUrl.searchParams.get("nim");
    response.statusCode = 200;
    response.setHeader("Content-Type", "text/html");
    response.end(`Ini Halaman Profilenya ${nim} <br><img src="https://simak.unismuh.ac.id/upload/mahasiswa/${nim}.jpg" alt="${nim}">`);
  }
  else{
    response.statusCode = 404;
    response.setHeader("Content-Type", "text/html");
    response.end("Halaman Tidak Ditemukan");

  }
  

});

server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});

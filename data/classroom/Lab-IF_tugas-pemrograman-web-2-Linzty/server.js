/*const http = require("http");

const hostname = "127.0.0.1";
const port = 3000;

const server = http.createServer((request, response) => {
  
  response.statusCode = 200;
  response.setHeader("Content-Type", "text/plain");
  response.end("Hello World");
});

server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});
*/

const http = require("http");
const fs = require("fs");

const hostname = "127.0.0.1";
const port = 3000;

const server = http.createServer((request, response) => {
  fs.readFile("index.html", (err, data) => {
    if (err) {
      response.statusCode = 500;
      response.setHeader("Content-Type", "text/plain");
      response.end("Internal Server Error");
    } else {
      response.statusCode = 200;
      response.setHeader("Content-Type", "text/html");
      response.end(data);
    }
  });
});

server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});


/*const http = require("http");

const hostname = "127.0.0.1";
const port = 3000;

const server = http.createServer((request, response) => {
  response.statusCode = 200;
  response.setHeader("Content-Type", "text/html");
  response.end(`
  <!DOCTYPE html>
  <html>
  <head>
    <title>Contoh Halaman HTML dengan JavaScript</title>
  </head>
  <body>
    <h1 id="judul">Selamat Datang!</h1>
  
    <button onclick="ubahTeks()">Klik untuk Mengubah Teks</button>
  
    <script>
      function ubahTeks() {
        document.getElementById("judul").innerHTML = "Halo, Dunia!";
      }
    </script>
  </body>
  </html>
  `);
});

server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});
*/
const http = require("http");

const server = http.createServer((request, response) => {
  const parsedUrl = new URL(request.url, `http://${request.headers.host}`);
  const params = parsedUrl.searchParams;

  if (parsedUrl.pathname === "/") {
    const nama = params.get("nama");
    const nim = params.get("nim");

    response.statusCode = 200;
    response.setHeader("Content-Type", "text/html");
    response.write("Nama mahasiswa: " + nama);
    response.write("<br>");
    response.write("NIM mahasiswa: " + nim);
    response.write("<br>");
    response.write("<img src='https://simak.unismuh.ac.id/upload/mahasiswa/" + nim + "_.jpg' width='200' height='200'>");
    response.end();
  } else {
    response.statusCode = 404;
    response.setHeader("Content-Type", "text/html");
    response.end("404 Not Found");
  }
});

const port = 3000;
const hostname = "127.0.0.1";

server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});
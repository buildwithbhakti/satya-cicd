const http = require("http");
const _ = require("lodash");

const PORT = process.env.PORT || 3000;

const server = http.createServer((req, res) => {
  const message = _.upperFirst("hello from the trivy demo");

  res.writeHead(200, { "Content-Type": "text/plain" });
  res.end(`${message}\n`);
});

server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

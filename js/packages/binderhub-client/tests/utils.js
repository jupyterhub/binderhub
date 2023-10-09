import http from "node:http";

/**
 *
 * @param {string} rawData Full text of the response to parse as EventSource formatted data
 */
export function parseEventSource(rawData) {
  let messages = [];
  for (const line of rawData.split("\n")) {
    const part = line.slice("data: ".length - 1);
    if (part.trim() !== "") {
      messages.push(JSON.parse(part));
    }
  }
  return messages;
}

/**
 *
 * @param {object} payloads
 * @returns {Promise}
 */
export async function simpleEventSourceServer(payloads) {
  return new Promise((resolve) => {
    const server = http.createServer(async (req, res) => {
      if (payloads[req.url]) {
        res.statusCode = 200;
        res.setHeader("Content-Type", "text/event-stream");
        // Setup CORS so jest can actually read the data
        res.setHeader("Access-Control-Allow-Origin", "*");
        res.flushHeaders();
        for (const line of payloads[req.url].split("\n")) {
          // Eventsource format requires newlines between each line of message
          res.write(line + "\n\n");
          // Wait at least 1ms between lines, to simulate all the data not arriving at once
          await new Promise((resolve) => setTimeout(resolve, 1));
        }
        res.end();
      } else {
        res.statusCode = 404;
        res.end();
      }
    });

    server.listen(0, "127.0.0.1", () => {
      resolve([
        `http://${server.address().address}:${server.address().port}`,
        () => server.close(),
      ]);
    });
  });
}

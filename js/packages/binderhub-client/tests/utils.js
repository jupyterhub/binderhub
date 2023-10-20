import { createServer } from "node:http";

/**
 * Parse an existing stored EventSource response body into an array of JSON objects
 *
 * @param {string} responseBody Full text of the response to parse as EventSource formatted data
 */
export function parseEventSource(responseBody) {
  let messages = [];
  for (const line of responseBody.split("\n")) {
    const part = line.slice("data: ".length - 1);
    if (part.trim() !== "") {
      messages.push(JSON.parse(part));
    }
  }
  return messages;
}

/**
 * Temporarily start a HTTP server to serve EventSource resources
 *
 * Returns the serverURL (including the protocol) where the server is listening, as well
 * as a function that can be used to stop the server.
 *
 * @param {object} fakeResponses Mapping of paths to response bodies (in EventSource format)
 *                               the server should respond with when those paths are requested. All
 *                               other paths will get a 404 response.
 * @returns {Promise}
 */
export async function simpleEventSourceServer(fakeResponses) {
  return new Promise((resolve) => {
    const server = createServer(async (req, res) => {
      if (fakeResponses[req.url]) {
        res.statusCode = 200;
        res.setHeader("Content-Type", "text/event-stream");
        // Setup CORS so jest can actually read the data
        res.setHeader("Access-Control-Allow-Origin", "*");
        res.flushHeaders();
        for (const line of fakeResponses[req.url].split("\n")) {
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

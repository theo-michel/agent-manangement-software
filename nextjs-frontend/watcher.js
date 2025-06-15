const chokidar = require("chokidar");
const { exec } = require("node:child_process");
const { config } = require("dotenv");

config({ path: ".env.local" });

const openapiFile = process.env.OPENAPI_OUTPUT_FILE;

// Check if the environment variable is defined
if (!openapiFile) {
  console.error("Error: OPENAPI_OUTPUT_FILE environment variable is not defined in .env.local");
  process.exit(1);
}

// Watch the specific file for changes
chokidar.watch(openapiFile).on("change", (path) => {
  console.log(`File ${path} has been modified. Running generate-client...`);
  exec("npm run generate-client", (error, stdout, stderr) => {
    if (error) {
      console.error(`Error: ${error.message}`);
      return;
    }
    if (stderr) {
      console.error(`stderr: ${stderr}`);
      return;
    }
    console.log(`stdout: ${stdout}`);
  });
});

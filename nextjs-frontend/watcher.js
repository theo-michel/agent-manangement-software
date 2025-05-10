const chokidar = require("chokidar");
const { exec } = require("node:child_process");
const { config } = require("dotenv");

config({ path: ".env.local" });

// Watch the specific file for changes
chokidar.watch("openapi.json").on("change", (path) => {
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

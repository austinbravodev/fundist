const path = require("path");

module.exports = {
  entry: {
    fundist: "./src/web/static/transpiled/fundist.js",
    fundist_signup: "./src/web/static/transpiled/fundist_signup.js",
  },
  output: {
    filename: "[name].min.js",
    path: path.resolve(__dirname, "src/web/static/dist"),
  },
};

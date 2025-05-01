const webpack = require("webpack");
const path = require("path");
const autoprefixer = require("autoprefixer");

const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = {
  mode: "development",
  context: path.resolve(__dirname, "binderhub/static"),
  entry: "./js/index.jsx",
  output: {
    path: path.resolve(__dirname, "binderhub/static/dist/"),
    filename: "bundle.js",
    publicPath: "auto",
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: "styles.css",
    }),
  ],
  resolve: {
    extensions: [".tsx", ".ts", ".js", ".jsx"],
  },
  module: {
    rules: [
      {
        test: /\.(t|j)sx?$/,
        exclude: /(node_modules|bower_components)/,
        use: {
          loader: "ts-loader",
        },
      },
      {
        test: /\.css$/i,
        use: [
          {
            loader: MiniCssExtractPlugin.loader,
            options: {
              // Set publicPath as relative path ("./").
              // By default it uses the `output.publicPath` ("/static/dist/"), when it rewrites the URLs in styles.css.
              // And it causes these files unavailabe if BinderHub has a different base_url than "/".
              publicPath: "./",
            },
          },
          "css-loader",
        ],
      },
      {
        test: /\.(scss)$/,
        use: [
          {
            loader: MiniCssExtractPlugin.loader,
            options: {
              // Set publicPath as relative path ("./").
              // By default it uses the `output.publicPath` ("/static/dist/"), when it rewrites the URLs in styles.css.
              // And it causes these files unavailabe if BinderHub has a different base_url than "/".
              publicPath: "./",
            },
          },
          "css-loader",
          {
            // Loader for webpack to process CSS with PostCSS
            loader: "postcss-loader",
            options: {
              postcssOptions: {
                plugins: [autoprefixer],
              },
            },
          },
          {
            // Loads a SASS/SCSS file and compiles it to CSS
            loader: "sass-loader",
          },
        ],
      },
      {
        test: /\.(eot|woff|ttf|woff2|svg|ico)$/,
        type: "asset/resource",
      },
    ],
  },
  devtool: "source-map",
};

const webpack = require('webpack');
const ExtractTextPlugin = require("extract-text-webpack-plugin");

module.exports = {
    context: __dirname + "/binderhub/static/",
    entry: "./js/index.js",
    output: {
        path: __dirname + "/binderhub/static/dist/",
        filename: "bundle.js",
        publicPath: '/static/dist/'
    },
    module: {
        rules: [
            {
                test: /\.css$/,
                use: ExtractTextPlugin.extract({
                    fallback: "style-loader",
                    use: "css-loader",
                    // Set publicPath as relative path ("./").
                    // By default it uses the `output.publicPath` ("/static/dist/"), when it rewrites the URLs in styles.css.
                    // And it causes these files unavailabe if BinderHub has a different base_url than "/".
                    publicPath: "./"
                })
            },
            {
                test: /\.(eot|woff|ttf|woff2|svg)$/,
                loader: "file-loader"
            }
        ]
    },
    devtool: 'source-map',
    plugins: [
        new webpack.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
        }),
        new ExtractTextPlugin("styles.css"),
    ]
}

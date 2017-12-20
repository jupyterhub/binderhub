var webpack = require('webpack');

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
                use: [ 'style-loader', 'css-loader' ]
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
        })
    ]
}

const stream = require('stream')

const React = require('react')
const ReactDOMServer = require('react-dom/server')
const Helmet = require('react-helmet').Helmet
const browserify = require('browserify')
const regeneratorRuntime = require("regenerator-runtime")  // Required for bundling

const templatePath = process.argv[2]

if (!templatePath) {
  throw new Error('Missing required argument: Path to template')
}

const context = process.argv[3] ? JSON.parse(process.argv[3]) : {}

// Load @babel/register so that we can compile React code in templatePath
require('@babel/register')({
  presets: ['@babel/preset-env', '@babel/preset-react']
})
const App = require(templatePath).default

const appHtml = ReactDOMServer.renderToString(React.createElement(App, {props: context}))
const helmet = Helmet.renderStatic()

const bundleString = `
  import React from 'react'
  import ReactDOM from 'react-dom'
  import App from '${templatePath}'

  ReactDOM.hydrate(React.createElement(App, {props: ${JSON.stringify(context)}}), document.getElementById("root"))
`

const strm = new stream.Transform()
strm.push(bundleString)
strm.push(null)
// TODO: Investigate faster bundling and minification
browserify(strm)
  .transform('babelify', {presets: ['@babel/preset-env', '@babel/preset-react']})
  .bundle((err, buf) => {
    if (err) {
      // TODO: Better error handling
      console.log(err)
      process.exit(1)
    } else {
      process.stdout.write(`
        <!DOCTYPE html>
        <html ${helmet.htmlAttributes.toString()}>
          <head>
            ${helmet.title.toString()}
            ${helmet.meta.toString()}
            ${helmet.link.toString()}
          </head>
          <body ${helmet.bodyAttributes.toString()}>
            <div id="root">${appHtml}</div>
          </body>
          <script type="text/javascript">${buf}</script>
        </html>`
      )
    }
  })

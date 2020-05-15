import stream from 'stream'

import React from 'react'
import ReactDOMServer from 'react-dom/server'
import { Helmet } from 'react-helmet'
import browserify from 'browserify'
import regeneratorRuntime from "regenerator-runtime"  // Required for bundling

const render = (templatePath, context) => {
  const App = require(templatePath).default
  const appHtml = ReactDOMServer.renderToString(<App props={context} />)
  const helmet = Helmet.renderStatic()

  const bundleString = `
    import React from 'react'
    import ReactDOM from 'react-dom'
    import App from '${templatePath}'

    ReactDOM.hydrate(<App props={${JSON.stringify(context)}} />, document.getElementById("root"))
  `

  const strm = new stream.Transform()
  strm.push(bundleString)
  strm.push(null)
  // TODO: Test for faster bundle times with Parcel
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
}

export default render

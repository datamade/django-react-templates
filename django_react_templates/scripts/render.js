import stream from 'stream'
import path from 'path'

import React from 'react'
import ReactDOMServer from 'react-dom/server'
import browserify from 'browserify'
import regeneratorRuntime from "regenerator-runtime";

const render = templatePath => {
  const App = require(templatePath).default
  // TODO: Pass in context here
  const appHtml = ReactDOMServer.renderToString(<App />)
  // TODO: Integrate Helmet for <head> management

  const bundleString = `
    import React from 'react'
    import ReactDOM from 'react-dom'
    import App from '${templatePath}'

    ReactDOM.hydrate(<App />, document.getElementById("root"))
  `

  const strm = new stream.Transform()
  strm.push(bundleString)
  strm.push(null)
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
          <html>
            <body>
              <div id="root">${appHtml}</div>
            </body>
            <script type="text/javascript">${buf}</script>
          </html>`
        )
      }
    })
}

export default render

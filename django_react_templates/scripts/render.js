import React from 'react'
import ReactDOMServer from 'react-dom/server'

const render = templatePath => {
  const App = require(templatePath).default
  // TODO: Pass in context here
  return ReactDOMServer.renderToString(<App />)
}

export default render

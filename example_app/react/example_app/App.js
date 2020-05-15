import React from 'react'
import { Helmet } from 'react-helmet'
import Home from './Home'

const App = ({props}) => (
  <>
    <Helmet>
      <meta charSet='utf-8' />
      <title>Example app</title>
    </Helmet>
    <Home name={props.name} />
  </>
)

export default App

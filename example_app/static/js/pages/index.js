import React from 'react'
import ReactDOM from 'react-dom'

const Home = (props) => (
  <>
    <div className="container-fluid mb-1 jumbotron">
      <div className="row">
        <div className="col-sm-10 offset-sm-1">
          <h1 className="mb-3">Django-React Integration</h1>
        </div>
      </div>
    </div>
    <div className="container">
      <div className="row pt-5 pb-4 text-center">
        <p>Welcome, {props.user}!</p>
      </div>
    </div>
  </>
)

ReactDOM.render(
  React.createElement(Home, window.props),
  window.reactMount,
)

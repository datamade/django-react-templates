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

    {"{% load static %}"}
    <a href="{% url 'client' %}">View client-side integration</a>
    <img src="{% static 'images/datamade-logo.png' %}" />

    {"{% csrf_token %}"}

    {"{% comment 'Comment out this code' %}"}
      <p>This code should be commented out</p>
    {"{% endcomment %}"}

    {"{% load i18n %}"}
    <p>{"{% trans 'This text should be translated.' %}"}</p>
    <p>
      {"{% blocktrans %}"}
        This text should also be translated.
      {"{% endblocktrans %}"}
    </p>
  </>
)

export default App

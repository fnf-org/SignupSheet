'use strict';

import Container from 'react-bootstrap/Container'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import Button from 'react-bootstrap/Button'
import ReactDOM from 'react-dom'
import React from 'react'
import Combobox from "react-widgets/Combobox";
import Cookies from 'js-cookie'
import DeleteButton from './deletejob.js'

import "react-widgets/styles.css";

const e = React.createElement;

class SignupButton extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      signup: true,
      emails: [],
      comment: '',
      user: null
    };
    this.handleClick = this.handleClick.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.updateSuggest = this.updateSuggest.bind(this);
  }

  handleClick(e) {
    e.preventDefault();
    this.setState({
      signup: ! this.state.signup
    })
  }

  handleSubmit(e) {
    e.preventDefault();
    if (this.state.user && this.state.emails.length === 0) {
      window.alert("The user you are trying to signup was not found.")
    }
    else {
      const csrftoken = Cookies.get('csrftoken');
      fetch('/signup/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
          'user': this.state.user,
          'jobid': this.props.job,
          'comment': this.state.comment 
        })
      }).then(response => {
        if (!response.ok) {
          window.confirm("There was an error signing up. Someone might have got there first or you're already busy at this time.")
        }
        location.reload()
      }).catch(error => {
        window.confirm("Something went wrong!")
        location.reload()
      })  
    }
  }

  updateSuggest(value) {
    if (value === "") {
      return
    }
    this.setState({user: value})
    fetch("/email_suggest/q=" + encodeURIComponent(value))
      .then(res => res.json())
      .then(
        (res) => {
          console.log("Update:", res.items)
          this.setState({
            emails: res.items
          });
        },
        // Note: it's important to handle errors here
        // instead of a catch() block so that we don't swallow
        // exceptions from actual bugs in components.
        (error) => {
          this.setState({
            emails: []
          });
        }
      )
  }

  show_default() {
    let delbutton = ""    
    if (this.props.signupid !== 'None') {
      delbutton = (
        <DeleteButton signupid={this.props.signupid} />
      )
    }

    if (this.props.volunteer === 'None') {
      if (this.props.can_signup) {
        return (
          <a onClick={this.handleClick}>Signup!</a>
        )  
      }
      else {
        return ""
      }
    }
    else {
      return (
      <>
        {this.props.volunteer} -- {this.props.comment} {delbutton}
      </>
      )
    }

  }

  show_signup() {
    var user_row = ""
    if (this.props.is_coordinator === "True") {
      user_row = (
        <Row style={{ paddingBottom: '1em' }} >
        <Col sm={12}>
          User:
          <Combobox
              hideCaret
              hideEmptyPopup
              filter="contains"
              placeholder="Search for email..."
              data={this.state.emails}
              onChange={this.updateSuggest}
          />
        </Col>
        </Row>
      )
    }
    return (
      <Container fluid={true}>
        {user_row}
        <Row style={{ paddingBottom: '1em' }} >
          <Col sm={12}>
            Comment:
            <input 
              style={{ width: '100%' }} 
              type="text" 
              value={this.state.comment} 
              onChange={(event) => {this.setState({'comment': event.target.value})}} 
            />
          </Col>
        </Row>
        <Row>
          <Col sm={2}><Button onClick={this.handleSubmit}>Submit</Button></Col>
          <Col sm={2}><Button variant='danger' onClick={this.handleClick}>Cancel</Button></Col>
        </Row>
      </Container>
    )
  }

  render() {
    if (this.state.signup) {
      return this.show_default()
    }
    else {
      return this.show_signup()
    }
  }
}

const domContainer = document.querySelectorAll('.jobsignup');
domContainer.forEach(
  element => {
    ReactDOM.render(e(SignupButton, { 
      'signupid': element.getAttribute('signupid'),
      'job': element.getAttribute('jobid'),
      'volunteer': element.getAttribute('volunteer'),
      'comment': element.getAttribute('comment'),
      'is_coordinator': element.getAttribute('is_coordinator'),
      'can_signup': element.getAttribute('can_signup') === 'True',
    }), element);
  }
)

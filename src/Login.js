import React, { Component } from 'react';
import './Login.scss';

const Mode = {
  LOG_IN: Symbol('LOG_IN'),
  CHANGE_PASSWORD: Symbol('CHANGE_PASSWORD'),
  FORGOT_PASSWORD: Symbol('FORGOT_PASSWORD')
};

export default class Login extends Component {
  constructor(props) {
    super(props);
    this.state = { user: '', password: '', password2: '', message: '', mode: Mode.LOG_IN, session: '', verificationCode: '' };
  }

  validateForm() {
    if (this.state.user.length > 0 && this.state.password.length > 0) {
      if (this.state.mode === Mode.CHANGE_PASSWORD) {
        return this.state.password === this.state.password2;
      } else if (this.state.mode === Mode.FORGOT_PASSWORD) {
        return this.state.password === this.state.password2 && this.state.verificationCode.length > 0;
      } else {
        return true;
      }
    }
    return false;
  }

  handleChange = event => {
    this.setState({ [event.target.id]: event.target.value });
  }

  get_auth_data(body) {
    const auth_data = {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      method: 'POST',
      body: body
    };
    return auth_data;
  }

  handleSubmit = event => {
    if (this.state.mode === Mode.CHANGE_PASSWORD) {
      this.send_password_change();
    } else if (this.state.mode === Mode.FORGOT_PASSWORD) {
      this.send_forgot_password();
    } else {
      this.send_auth();
    }
    event.preventDefault();
  }

  handleResponse = data => {
    if (data.hasOwnProperty('IdToken')) {
      this.props.onLogin(data.IdToken, data.AccessToken);
    } else if (data.hasOwnProperty('message')) {
      this.setState({ message: data.message });
    } else if (data.hasOwnProperty('passwordChangeSuccessful')) {
      this.setState({ message: 'password changed successfully', password: '', password2: '', mode: Mode.LOG_IN, session: '', verificationCode: ''  });
    } else if (data.hasOwnProperty('passwordResetRequired') && data.passwordResetRequired) {
      this.setState({ mode: Mode.FORGOT_PASSWORD, message: 'reset required', password: '' });
    } else if (data.hasOwnProperty('ChallengeName') && data.ChallengeName ===  'NEW_PASSWORD_REQUIRED' && data.hasOwnProperty('Session')) {
      this.setState({ mode: Mode.CHANGE_PASSWORD, session: data.Session, password: '', message: 'password change required' });
    } else {
      this.setState({ message: 'unknown login error' });
    }
  }

  send_password_change() {
    if (this.validateForm()) {
      const auth_data = this.get_auth_data('{"user":"' + this.state.user + '","password":"' + this.state.password + '","Session":"' + this.state.session + '"}');
      fetch(this.props.newPassUrl, auth_data).then(r => r.json())
        .then(this.handleResponse)
        .catch(e => console.error(e));
    }
  }

  send_forgot_password() {
    if (this.validateForm()) {
      const auth_data = this.get_auth_data('{"user":"' + this.state.user + '","password":"' + this.state.password + '","verificationCode":"' + this.state.verificationCode + '"}');
      console.log(auth_data);
      fetch(this.props.newPassUrl, auth_data).then(r => r.json())
        .then(this.handleResponse)
        .catch(e => console.error(e));
    }
  }

  send_auth = () => {
    if (this.validateForm()) {
      const auth_data = this.get_auth_data('{"user":"' + this.state.user + '","password":"' + this.state.password + '"}');
      fetch(this.props.authUrl, auth_data).then(r => r.json())
        .then(this.handleResponse)
        .catch(e => console.error(e));
    }
  }

  render() {
    let repeatPass = [];
    let actionText = 'Log in';
    if (this.state.mode === Mode.CHANGE_PASSWORD) {
      repeatPass = [<input id="password2" type="password" placeholder="Repeat Password" onChange={this.handleChange} key={0}/>, <i className="fa fa-key" key={1}></i>];
      actionText = 'Change password';
    } else if (this.state.mode === Mode.FORGOT_PASSWORD) {
      repeatPass = [<input id="password2" type="password" placeholder="Repeat Password" onChange={this.handleChange} key={0}/>, <i className="fa fa-key" key={1}></i>,
                    <input id="verificationCode" type="text" placeholder="Verification Code" onChange={this.handleChange} key={2}/>, <i className="fa fa-unlock" key={3}></i>];
      actionText = 'Reset password';
    }

    return (
      <div className="wrapper">
        <form className="login" onSubmit={this.handleSubmit}>
          <p className="title">{actionText}</p>
          <input id="user" type="text" placeholder="Username" onChange={this.handleChange} autoFocus/>
          <i className="fa fa-user"></i>
          <input id="password" type="password" placeholder="Password" value={this.state.password} onChange={this.handleChange}/>
          <i className="fa fa-key"></i>
          {repeatPass}
          <button disabled={!this.validateForm()}>
            <span className="state">{actionText}</span>
          </button>
        </form>
        <span className="message">{this.state.message}</span>
    </div>
    );
  }
}

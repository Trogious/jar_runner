import React from 'react';
import './App.css';
import Login from './Login'
import Jar from './Jar'

export default class App extends React.Component {
  constructor (props) {
    // console.log("constructor");
    super(props);
    let cachedToken = localStorage.getItem('token');
    if (cachedToken === null) {
      cachedToken = ''
    }
    const cachedJars = JSON.parse(localStorage.getItem('jars'));
    // const cachedJars = JSON.parse('["SampleGame2.jar","SampleGame3.jar","SampleGame4.jar"]');
    // cachedToken = 'x';
    this.state = { token: cachedToken, message: '', jars: cachedJars };

    this.list_url = 'JAR_API_ENDPOINT_LIST_JARS';
    this.auth_url = 'JAR_API_ENDPOINT_AUTH';
    this.newpass_url = 'JAR_API_ENDPOINT_NEWPASS';
    this.schedule_url = 'JAR_API_ENDPOINT_SCHEDULE';
    this.params = JSON.parse('JAR_EXEC_PARAMS_CONFIG');
    // this.params = JSON.parse('{"params":[{"name":"threads","type":"int","min":1,"max":16,"default":8},{"name":"spins","type":"string","allowed":["500k","100m","500m","1b"],"default":"500m"}],"spacing":{"param":":","value":"="}}');
  }

  fetchJarList() {
    if (this.state.token !== '') {
      const auth_data = {
        headers: {
          'Accept': 'application/json',
          'Authorization': this.state.token
        }
      };
      let status = 0;
      fetch(this.list_url, auth_data)
        .then(r => {status = r.status; return r.json();})
        .then(data => {
          console.log(data);
          if (data.hasOwnProperty('jars')) {
            localStorage.setItem('jars', JSON.stringify(data.jars));
            this.setState({ jars: data.jars, message: '' });
          } else if (data.hasOwnProperty('message')) {
            if (status === 403) {
              this.setState({ message: data.message, jars: null, token: '' });
            } else {
              this.setState({ message: data.message, jars: [] });
            }
          }
        })
      .catch(e => console.error(e));
    }
  }

  onLogin = (t,a) => {
    localStorage.setItem('token', t);
    this.setState({ token: t, message: '' });
    this.fetchJarList();
  }

  onError = m => {
    this.setState({message: m});
  }

  handleSubmitJar = e => {
    const auth_data = {
      headers: {
        'Accept': 'application/json',
        'Authorization': this.state.token
      },
      method: 'POST',
      body: '{"name": "' + e.target.jar.value + '"}'
    };
    console.log(auth_data);
    let status = 0;
    fetch(this.schedule_url, auth_data)
      .then(r => {status = r.status; return r.json();})
      .then(data => {
        console.log(data);
        if (data.hasOwnProperty('status')) {
          this.setState({ message: data.status });
        } else if (data.hasOwnProperty('message')) {
          if (status === 403) {
            this.setState({ message: data.message });
          } else {
            this.setState({ message: data.message });
          }
        }
      })
    .catch(e => console.error(e));
    e.preventDefault();
  }


  render() {
    console.log('render');
    if (this.state.token === '')
    {
      return (<Login authUrl={this.auth_url} newPassUrl={this.newpass_url} onLogin={this.onLogin} onError={this.onError}/>);
    }
    else if (this.state.jars === null) {
      return (<div className="App">{this.state.message}</div>);
    } else {
      return (
        <div>
          <div>
            <form onSubmit={this.handleSubmitJar}>
              <table>
                <thead>
                  <tr>
                    <th>Artifact</th>
                    <th colSpan={this.params.params.length}>Parameters</th>
                    <th>Action</th>
                  </tr>
                </thead>
                {this.state.jars.map((jar, i) => <Jar key={i} name={jar} params={this.params} submit={this.handleSubmitJar} />)}
              </table>
            </form>
          </div>
          <div className="logout">
            <form onSubmit={() => {this.setState({ token: '' });localStorage.setItem('token', '');}}>
              <button>Logout</button>
            </form>
          </div>
          <div>
            {this.state.message}
          </div>
        </div>
      );
    }
  }
}

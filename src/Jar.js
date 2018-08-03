import React from 'react'
import Param from './Param'
import './Jar.scss'

export default class Jar extends React.Component {
  constructor(props) {
    super(props);
    const paramsValues = {};
    const params = this.props.params.params;
    for (let i = 0; i < params.length; ++i) {
      paramsValues[params[i].name] = params[i].default;
    }
    this.state = {...paramsValues};
  }
  getParamsString(name, params, spacing, idxWithValue, value) {
    let paramsString = 'java -jar ./' + name + ' ';
    for (let i = 0; i < params.length; ++i) {
      if (i > 0) {
        paramsString += spacing.param;
      }
      paramsString += params[i].name + spacing.value + this.state[params[i].name];
    }
    return paramsString;
  }

  onChangeParam = (jarName, paramIdx, value) => {
    const paramValuePair = {};
    paramValuePair[this.props.params.params[paramIdx].name] = value;
    this.setState(paramValuePair);
  }

  handleSubmit = (e) => {
    const params = JSON.stringify(this.state);
    this.props.submit(this.props.name, params);
    e.preventDefault();
  }

  render() {
    return (
      <div>
        <div className="row">
          <form onSubmit={this.handleSubmit}>
          <div className="cell">
            <div className="content">
              <input name="jar" type="hidden" value={this.props.name}/>{this.props.name}
            </div>
          </div>
          <div className="cell">
            <div className="content">
              {this.props.params.params.map((param, i) => <Param key={i} paramIdx={i} jar={this.props.name} {...param} paramChanged={this.onChangeParam}/>)}
            </div>
          </div>
          <div className="cell">
            <div className="content">
            <button>
              <span>Schedule Execution</span>
            </button>
            </div>
          </div>
        </form>
        </div>
        <div className="row rowno">
          <div className="cell cell2">
            <div className="content">
              Execution command preview:
              <div className="exec">
               <pre className="preview">{this.getParamsString(this.props.name, this.props.params.params, this.props.params.spacing)}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

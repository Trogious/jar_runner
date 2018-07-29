import React from 'react'
import Param from './Param'
import './Jar.css'

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
    let paramsString = 'java -jar ' + name + ' ';
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

  render() {
    return (
      <tbody>
        <tr>
          <td><input name='jar' type='hidden' value={this.props.name}/>{this.props.name}</td>
          {this.props.params.params.map((param, i) => <Param key={i} paramIdx={i} jar={this.props.name} {...param} paramChanged={this.onChangeParam}/>)}
          <td>
            <button>
              <span>Schedule Execution</span>
            </button>
          </td>
        </tr>
        <tr>
          <td colSpan={this.props.params.params.length+2} className='tdExecPrev'>
            <p>Execution command preview:</p>
            <pre className='exec_preview'>{this.getParamsString(this.props.name, this.props.params.params, this.props.params.spacing)}</pre>
          </td>
        </tr>
      </tbody>
    );
  }
}

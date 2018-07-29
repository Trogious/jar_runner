import React from 'react'

export default class Param extends React.Component {
  paramChangedInt = (event) => {
    let value = Math.max(Math.min(event.target.value, this.props.max), this.props.min);
    this.props.paramChanged(this.props.jar, this.props.paramIdx, value);
    event.preventDefault();
  }

  paramChangedString = (event) => {
    this.props.paramChanged(this.props.jar, this.props.paramIdx, event.target.value);
    event.preventDefault();
  }

  render() {
    switch (this.props.type) {
      case 'int':
        const defaultValue = this.props.default === undefined ? this.props.min : this.props.default;
        return (
          <td>
            {this.props.name}:
            <input name={this.props.name} type='number' min={this.props.min} max={this.props.max} defaultValue={defaultValue} onChange={this.paramChangedInt}/>
          </td>
        );
      default:
        if (this.props.allowed !== undefined && this.props.allowed.length > 0) {
          const defaultValue = this.props.default === undefined ? this.props.allowed[0] : this.props.default;
          return (
            <td>
              {this.props.name}:
              <select name={this.props.name} defaultValue={defaultValue} onChange={this.paramChangedString}>
                {this.props.allowed.map((value, i) => <option key={i} value={value}>{value}</option>)}
              </select>
            </td>
          );
        }
        else {
          const defaultValue = this.props.default === undefined ? '' : this.props.default;
          return (
            <td>
              {this.props.name}:
              <input name={this.props.name} type='text' defaultValue={defaultValue} onChange={this.paramChangedString}/>
            </td>
          );
        }
    }
  }
}

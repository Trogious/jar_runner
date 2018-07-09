import React from 'react'

export default class Jar extends React.Component {
  render() {
    return (
      <div>
        <form onSubmit={this.props.submit}>
          <p>{this.props.name}</p>
          <input name="jar" type="hidden" value={this.props.name}/>
          <button>
            <span>Schedule RTP</span>
          </button>
        </form>
      </div>
    );
  }
}

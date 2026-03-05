import React from 'react'
import ErrorState from '../states/ErrorState/ErrorState'

type Props = {
  children: React.ReactNode
}

type State = {
  error: Error | null
}

export default class ErrorBoundary extends React.Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error) {
    return { error }
  }

  render() {
    if (this.state.error) {
      return <ErrorState title='App crashed' message={this.state.error.message || 'Unknown error'} />
    }
    return this.props.children
  }
}

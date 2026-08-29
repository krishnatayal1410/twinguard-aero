import React from"react";
type Props={children:React.ReactNode;name?:string;fallback?:React.ReactNode};
type State={error?:Error};
export default class ErrorBoundary extends React.Component<Props,State>{
 state:State={};
 static getDerivedStateFromError(error:Error){return{error}}
 componentDidCatch(error:Error,info:React.ErrorInfo){console.error(`[TwinGuard] ${this.props.name??"component"} failed`,error,info)}
 render(){
  if(!this.state.error)return this.props.children;
  return this.props.fallback??<div className="component-fallback"><strong>{this.props.name??"Component"} unavailable</strong><span>{this.state.error.message}</span><button onClick={()=>this.setState({error:undefined})}>Retry</button></div>
 }
}
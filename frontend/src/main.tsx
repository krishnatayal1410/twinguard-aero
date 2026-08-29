import React from"react";import ReactDOM from"react-dom/client";import App from"./App";import ErrorBoundary from"./components/ErrorBoundary";import AuthGate from"./components/AuthGate";
const root=document.getElementById("root");
if(!root)throw new Error("TwinGuard root element is missing");
ReactDOM.createRoot(root).render(<React.StrictMode><ErrorBoundary name="TwinGuard Aero" fallback={<div style={{padding:32,fontFamily:"system-ui",color:"#15304c"}}><h2>TwinGuard Aero could not start</h2><p>Reload the page. If this remains visible, run <code>bash scripts/doctor.sh</code> and check the frontend log.</p></div>}><AuthGate><App/></AuthGate></ErrorBoundary></React.StrictMode>);
